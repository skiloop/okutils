#include <cstring>
#include <cstdlib>
#include <sys/stat.h>

#ifdef _WIN32
#include <cstdint>
#include <windows.h>
typedef struct _stat64 FStat;
#else
#include <sys/file.h>
#include <unistd.h>
typedef struct stat FStat;
#endif

int64_t mp_append_log(const char * logfile, const char * logs, int len)
{
	if (!logfile || !logs || !*logfile || len < 0)
		return -2;

	FStat st;
	memset(&st, 0, sizeof(st));
#ifdef _WIN32
	HANDLE hFile;
	{
		DWORD desiredAccess = GENERIC_WRITE;
		DWORD shareMode = FILE_SHARE_READ;
		DWORD creationDisposition = OPEN_ALWAYS;
		DWORD flagsAndAttributes = FILE_ATTRIBUTE_NORMAL;

		// open file
		hFile =  CreateFile(
				logfile,               // filename
				desiredAccess,         // mode
				shareMode,             // share mode
				NULL,                  //
				creationDisposition,   // how to create
				flagsAndAttributes,    // attributes
				NULL);                 //
		if (hFile == INVALID_HANDLE_VALUE)
			return -1;
	}
	_stat64(logfile, &st);
	//lock area
	OVERLAPPED overlapped = {0};
	overlapped.Offset = 0;
	overlapped.OffsetHigh = 0;
	LockFileEx(hFile, LOCKFILE_EXCLUSIVE_LOCK, 0, 1, 0x7FFFFFFF, &overlapped);

	// write file
	int wr = WriteFile(hFile, logs, (DWORD)strlen(logs), NULL, NULL);
	UnlockFileEx(hFile, 0, 1, 0x7FFFFFFF, &overlapped);
	CloseHandle(hFile);

#else

	int fd = open(logfile, O_APPEND|O_CREAT|O_WRONLY, 0644);

	if (fd < 0)
		return -1;

	flock(fd, LOCK_EX);

	fstat(fd, &st);
	write(fd, logs, len);
	//fsync(fd);
	flock(fd, LOCK_UN);
	close(fd);
#endif
	static_assert(sizeof(st.st_size)==8, "must support large file.");

	return st.st_size;
}
