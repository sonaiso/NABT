#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
/* The runtime virtualizes getpid(), but /proc/self/exe resolves correctly.
   Rewrite only the caller's own numeric executable link, nothing else. */
ssize_t readlink(const char *path, char *buf, size_t bufsiz) {
  static ssize_t (*real_readlink)(const char *, char *, size_t);
  if (!real_readlink) real_readlink = dlsym(RTLD_NEXT, "readlink");
  if (!real_readlink) { errno = ENOSYS; return -1; }
  char own[64];
  snprintf(own, sizeof own, "/proc/%d/exe", (int)getpid());
  return real_readlink(strcmp(path, own) == 0 ? "/proc/self/exe" : path, buf, bufsiz);
}
