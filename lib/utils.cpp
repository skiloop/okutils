
#include <boost/python.hpp>
int64_t mp_append_log(const char * logfile, const char * logs, int len);
using namespace boost::python;
int64_t mp_append_log_wrapper(const char * logfile, std::string const &logs){
    return mp_append_log(logfile, logs.c_str(), logs.length());
}

BOOST_PYTHON_MODULE (tools) {
//    def("mp_append_log", &mp_append_log, (arg("logfile"), arg("logs") , arg("size")),"append content to logfile");
    def("mp_append_log", &mp_append_log_wrapper, "append content to logfile");
}