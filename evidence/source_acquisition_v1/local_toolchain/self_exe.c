#define _GNU_SOURCE
#include <unistd.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
/* This sandbox exposes /proc/self/exe but not /proc/<pid>/exe.
   Redirect only the current process executable link; all else unchanged. */
ssize_t readlink(const char *path, char *buf, size_t size) {
  static ssize_t (*real_readlink)(const char*, char*, size_t);
  if (!real_readlink) real_readlink = dlsym(RTLD_NEXT, "readlink");
  char self[80]; snprintf(self, sizeof(self), "/proc/%ld/exe", (long)getpid());
  return real_readlink(strcmp(path,self)==0 ? "/proc/self/exe" : path, buf, size);
}
