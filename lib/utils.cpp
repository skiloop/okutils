
#include <boost/python.hpp>
int64_t mp_append_log(const char * logfile, const char * logs, int len);
BOOST_PYTHON_MODULE (tools) {
    using namespace boost::python;
    def("mp_append_log", &mp_append_log, (arg("logfile"), arg("logs") , arg("size")),"append content to logfile");
}