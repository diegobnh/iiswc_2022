
#include <libsyscall_intercept_hook_point.h>
//#include "/ihome/dmosse/dmoura/0_tools/syscall/syscall_intercept/include/libsyscall_intercept_hook_point.h"
#include <syscall.h>
#include <errno.h>
#include <stdio.h>
#include <execinfo.h>
#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#define _GNU_SOURCE
#include <pthread.h>
#define SIZE 4096
#include <sys/resource.h> 
#include <numaif.h>

FILE *g_fp=NULL;
char *g_line = NULL;
size_t len = 0;

pthread_mutex_t count_mutex;

long int hash (char* word)
{
    unsigned int hash = 0;
    for (int i = 0 ; word[i] != '\0' ; i++)
    {
        hash = 31*hash + word[i];
    }
    //return hash % TABLE_SIZE;
    return abs(hash) ;
}

void
redirect_stdout (char *filename)
{
    int fd;
    if ((fd = open(filename,O_CREAT|O_WRONLY,0666)) < 0){
	    perror(filename);
	    exit(1);
    }
    close(1);
    if (dup(fd) !=1){
        fprintf(stderr,"Unexpected dup failure\n");
	exit(1);
    }
    close(fd);

    g_fp = fopen("call_stack.txt", "w+");
    if(g_fp == NULL){
        printf("Error when try to use fopen!!\n");
    }
}

void get_call_stack (int size_allocation, char *call_stack_concat) {
    int static mmap_id=0;
    int nptrs;
    void *buffer[SIZE];
    ssize_t read;
    char *addr;
    char size[20]="";
    int j;
    char **strings;

    nptrs = backtrace(buffer, SIZE);
    backtrace_symbols_fd(buffer, nptrs,STDOUT_FILENO);
    fflush(stdout);

    int i; // callstack_line_index;
    int k=0;
    const char* substring = getenv("APP");

    char *p;
    //while ((read = getline(&g_line, &len, g_fp)) != -1) {
    for(int callstack_line_index=0; callstack_line_index < nptrs; callstack_line_index++){
        read = getline(&g_line, &len, g_fp);
        p = strstr(g_line,substring);

        if(p){
          for(i=0;i<len;i++)
          {
	  	if(g_line[i] == '[')
		{
		     break;
		}
          }
          for(i=i+1; i<len;i++)
          {
		if(g_line[i] ==']')
                    break;
                call_stack_concat[k] = g_line[i];
                k++;
	  }
          call_stack_concat[k] = ':';
          k++;
       }
    }
    call_stack_concat[k-1] = '\0';
    strcat(call_stack_concat,size);
}


static int hook (long syscall_number, long arg0, long arg1, long arg2, long arg3, long arg4, long arg5,	long *result)
{
    int static mmap_id=0;
    struct timespec ts;
    char call_stack_concat[SIZE]="";
    static unsigned long g_nodemask;

    if (syscall_number == SYS_mmap) {

	/* pass it on to the kernel */
	*result = syscall_no_intercept(syscall_number, arg0, arg1, arg2, arg3, arg4, arg5);

	pthread_mutex_lock(&count_mutex);
	clock_gettime(CLOCK_MONOTONIC, &ts);
	get_call_stack(arg1,call_stack_concat);
	fprintf(stderr, "%ld.%ld,mmap, %ld, %p,%ld,%s\n",ts.tv_sec,ts.tv_nsec,arg1,(void *)*result,hash(call_stack_concat),call_stack_concat);
	pthread_mutex_unlock(&count_mutex);

        if (arg1 > 10e10){
    	    g_nodemask = 4;
        }else {
	    g_nodemask = 1;
        }
	    
	if (mbind((void *)*result, (unsigned long)arg1, MPOL_BIND, &g_nodemask, 64, MPOL_MF_MOVE) == -1)
        {
            fprintf(stderr,"Error:%d\n",errno);
            perror("Error description");
        }
	return 0;
    }else if (syscall_number == SYS_munmap){
	/* pass it on to the kernel */
	*result = syscall_no_intercept(syscall_number, arg0, arg1, arg2, arg3, arg4, arg5);
	clock_gettime(CLOCK_MONOTONIC, &ts);
	fprintf(stderr, "%ld.%ld,munmap,%p,%ld\n", ts.tv_sec,ts.tv_nsec, (void *)arg0, arg1);
	return 0;
    }else {
	/*
	 * Ignore any other syscalls
	 * i.e.: pass them on to the kernel
	 * as would normally happen.
	 */
	return 1;
    }
}

static __attribute__((constructor)) void init(int argc, char * argv[])
{
    setvbuf(stdout, NULL, _IONBF, 0);  //avoid buffer from printf
    redirect_stdout("call_stack.txt");

    intercept_hook_point = hook;
}
