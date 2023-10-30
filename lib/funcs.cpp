#include <cstring>
#include <cstdlib>
#ifdef _WIN32
#else
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

int64_t mp_append_log(const char * logfile, const char * logs, int len)
{
	if (!logfile || !logs || !*logfile || len < 0)
		return -2;

	struct stat st;
	memset(&st, 0, sizeof(st));
	int fd = open(logfile, O_APPEND|O_CREAT|O_WRONLY, 0644);
	if (fd < 0)
		return -1;

	flock(fd, LOCK_EX);
	fstat(fd, &st);
	write(fd, logs, len);
	//fsync(fd);
	flock(fd, LOCK_UN);
	close(fd);
	static_assert(sizeof(st.st_size)==8, "must support large file.");
	return st.st_size;
}
