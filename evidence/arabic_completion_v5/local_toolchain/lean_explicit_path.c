#include <lean/lean.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>

/* Uses the official Lean shared library without patching it. Only the shell
 * bootstrap is replaced: initSearchPath receives the verified installation
 * directory explicitly instead of asking IO.appPath. All option handling,
 * elaboration, proof checking and compilation remain the official Lean code. */
extern void lean_initialize(void);
extern lean_obj_res l_Lean_initSearchPath(lean_obj_arg, lean_obj_arg);
extern lean_obj_res lean_enable_initializer_execution(void);
extern lean_obj_res lean_shell_options_mk(lean_obj_arg);
extern lean_obj_res lean_shell_options_process(lean_obj_arg, uint32_t, lean_obj_arg);
extern uint32_t lean_shell_options_get_num_threads(lean_obj_arg);
extern uint8_t lean_shell_options_get_run(lean_obj_arg);
extern lean_obj_res lean_shell_main(lean_obj_arg, lean_obj_arg);

static const struct option options[] = {
 {"version",0,0,'v'}, {"short-version",0,0,'V'}, {"githash",0,0,'g'},
 {"help",0,0,'h'}, {"features",0,0,'f'}, {"stdin",0,0,'I'},
 {"run",0,0,'r'}, {"deps",0,0,'d'}, {"src-deps",0,0,'O'},
 {"deps-json",0,0,'N'}, {"json",0,0,'J'}, {"stats",0,0,'a'},
 {"profile",0,0,'P'}, {"olean",1,0,'o'}, {"ilean",1,0,'i'},
 {"root",1,0,'R'}, {"threads",1,0,'j'}, {"memory",1,0,'M'},
 {"timeout",1,0,'T'}, {"tstack",1,0,'s'}, {"trust",1,0,'t'},
 {"c",1,0,'c'}, {"bc",1,0,'b'}, {"plugin",1,0,'p'},
 {"load-dynlib",1,0,'l'}, {"setup",1,0,'u'}, {"error",1,0,'E'},
 {"incr-save",1,0,'Y'}, {"incr-load",1,0,'Z'},
 {"incr-header-save",1,0,'H'}, {0,0,0,0}
};

int main(int argc, char **argv) {
    struct rlimit stack;
    if (!getrlimit(RLIMIT_STACK, &stack) && stack.rlim_cur < 64UL*1024*1024) {
      stack.rlim_cur = stack.rlim_max < 64UL*1024*1024 ? stack.rlim_max : 64UL*1024*1024;
      setrlimit(RLIMIT_STACK, &stack);
    }
    lean_initialize();
    lean_object *result = l_Lean_initSearchPath(
      lean_mk_string("/tmp/nabt-tools/lean-4.34.1-linux"), lean_box(0));
    if (lean_io_result_is_error(result)) {
      lean_io_result_show_error(result); lean_dec(result); return 1;
    }
    lean_dec(result);
    lean_dec(lean_enable_initializer_execution());
    lean_object *opts = lean_shell_options_mk(lean_box(0));
    int opt;
    while ((opt=getopt_long(argc,argv,"vVghfIrdONJaPqo:i:R:j:M:T:s:t:c:b:D:p:l:u:E:Y:Z:H:",options,NULL))!=-1) {
      if (opt == '?') return 2;
      lean_object *arg = lean_box(0);
      if (optarg) {
        arg = lean_alloc_ctor(1,1,0); lean_ctor_set(arg,0,lean_mk_string(optarg));
      }
      result=lean_shell_options_process(opts,(uint32_t)opt,arg);
      if (lean_io_result_is_error(result)) {
        int code=(int)lean_unbox_uint32(lean_io_result_get_error(result));
        lean_dec(result); return code;
      }
      opts=lean_io_result_take_value(result);
      lean_inc(opts);
      if (lean_shell_options_get_run(opts)) break;
    }
    lean_io_mark_end_initialization();
    lean_inc(opts);
    lean_init_task_manager_using(lean_shell_options_get_num_threads(opts));
    lean_object *args=lean_box(0);
    for (int i=argc-1;i>=optind;i--) {
      lean_object *cons=lean_alloc_ctor(1,2,0);
      lean_ctor_set(cons,0,lean_mk_string(argv[i]));
      lean_ctor_set(cons,1,args); args=cons;
    }
    result=lean_shell_main(args,opts);
    int code;
    if (lean_io_result_is_error(result)) {
      lean_io_result_show_error(result); code=1;
    } else code=(int)lean_unbox_uint32(lean_io_result_get_value(result));
    lean_dec(result);
    lean_finalize_task_manager();
    return code;
}
