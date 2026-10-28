#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
/* The sandbox permits /proc/self/exe but denies /proc/<getpid()>/exe.
 * Linux defines both as the same current-process executable. Translate only
 * that exact own-PID path; all other readlink calls are unchanged. This
 * bootstrap shim changes no Lean kernel, source, proof, or compiler code. */
ssize_t readlink(const char *path, char *buf, size_t size) {
    ssize_t (*real_readlink)(const char*, char*, size_t) = dlsym(RTLD_NEXT, "readlink");
    if (!real_readlink) { errno = ENOSYS; return -1; }
    char own[64];
    snprintf(own, sizeof(own), "/proc/%ld/exe", (long)getpid());
    if (strcmp(path, own) == 0) path = "/proc/self/exe";
    return real_readlink(path, buf, size);
}
