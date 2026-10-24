/* Use Lean's public initSearchPath with an explicit toolchain root.
   No runtime/kernel/library patching; no procfs access is needed. */
#include <lean/lean.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
extern void lean_initialize(void);
extern void lean_enable_initializer_execution(void);
extern lean_object *l_Lean_initSearchPath(lean_object *, lean_object *);
extern lean_object *lean_shell_options_mk(lean_object *);
extern lean_object *lean_shell_options_process(lean_object *, uint32_t, lean_object *);
extern lean_object *lean_shell_main(lean_object *, lean_object *);
static lean_object *unwrap(lean_object *r) {
  if (lean_io_result_is_error(r)) { lean_io_result_show_error(r); exit(1); }
  lean_object *v = lean_io_result_get_value(r); lean_inc(v); lean_dec(r); return v;
}
int main(int argc, char **argv) {
  fprintf(stderr,"init\n"); lean_initialize(); fprintf(stderr,"path\n");
  lean_dec(unwrap(l_Lean_initSearchPath(lean_mk_string("/tmp/nabt-classical-tools/lean-4.34.1-linux"),lean_box(0))));
  fprintf(stderr,"options\n"); lean_enable_initializer_execution();
  lean_object *opts=lean_shell_options_mk(lean_box(0));
  int first=1;
  for (;first<argc && argv[first][0]=='-';first++) {
    char flag=argv[first][1]; lean_object *arg=lean_box(0);
    if (!strcmp(argv[first],"--version")) flag='v';
    else if (!strcmp(argv[first],"--run")) flag='r';
    else if (flag=='o'||flag=='c'||flag=='R'||flag=='D') {
      if (++first>=argc) return 2;
      arg=lean_alloc_ctor(1,1,0); lean_ctor_set(arg,0,lean_mk_string(argv[first]));
    } else {fprintf(stderr,"Unsupported driver option\n"); return 2;}
    lean_object *r=lean_shell_options_process(opts,flag,arg);
    if (lean_io_result_is_error(r)) return lean_unbox(lean_io_result_get_error(r));
    opts=unwrap(r);
  }
  lean_io_mark_end_initialization(); lean_init_task_manager();
  lean_object *args=lean_box(0);
  for(int i=argc-1;i>=first;i--) {lean_object *next=lean_alloc_ctor(1,2,0);lean_ctor_set(next,0,lean_mk_string(argv[i]));lean_ctor_set(next,1,args);args=next;}
  lean_object *r=unwrap(lean_shell_main(args,opts));
  return lean_unbox(r);
}
