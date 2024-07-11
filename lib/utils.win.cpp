#include <Python.h>
int64_t mp_append_log(const char * logfile, const char * logs, int len);

static PyObject* mp_append_log_wrapper(PyObject* self, PyObject* args) {
    const char* filename;
    const char* logs;
    if (!PyArg_ParseTuple(args, "ss", &filename, &logs)) {
        return NULL;
    }
    int64_t result = mp_append_log(filename, logs, strlen(logs));
    return PyLong_FromLong(result);
}

static PyMethodDef Methods[] = {
    {"mp_append_log",  mp_append_log_wrapper, METH_VARARGS, "append content to logfile"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef tools = {
    PyModuleDef_HEAD_INIT,
    "tools",   /* name of module */
    NULL, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    Methods
};

PyMODINIT_FUNC PyInit_tools(void) {
    return PyModule_Create(&tools);
}