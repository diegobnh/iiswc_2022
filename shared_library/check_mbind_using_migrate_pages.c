//#include <libsyscall_intercept_hook_point.h>
#include "/ihome/dmosse/dmoura/0_tools/syscall/syscall_intercept/include/libsyscall_intercept_hook_point.h"
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
#include <numa.h>


/*

This is the output example:

DRAM:1, NOT_DRAM:0, NOT_ALLOCATED:33246298, Ratio_DRAM:0.00
DRAM:1, NOT_DRAM:0, NOT_ALLOCATED:33246298, Ratio_DRAM:0.00
DRAM:873780, NOT_DRAM:0, NOT_ALLOCATED:32372519, Ratio_DRAM:0.03
DRAM:2953765, NOT_DRAM:0, NOT_ALLOCATED:30292534, Ratio_DRAM:0.09
DRAM:4325866, NOT_DRAM:0, NOT_ALLOCATED:28920433, Ratio_DRAM:0.13
DRAM:6358530, NOT_DRAM:0, NOT_ALLOCATED:26887769, Ratio_DRAM:0.19
DRAM:7549682, NOT_DRAM:0, NOT_ALLOCATED:25696617, Ratio_DRAM:0.23
DRAM:8746224, NOT_DRAM:0, NOT_ALLOCATED:24500075, Ratio_DRAM:0.26
DRAM:10083815, NOT_DRAM:0, NOT_ALLOCATED:23162484, Ratio_DRAM:0.30
DRAM:11870698, NOT_DRAM:0, NOT_ALLOCATED:21375601, Ratio_DRAM:0.36
DRAM:13075702, NOT_DRAM:0, NOT_ALLOCATED:20170597, Ratio_DRAM:0.39
DRAM:14284773, NOT_DRAM:0, NOT_ALLOCATED:18961526, Ratio_DRAM:0.43
DRAM:15496163, NOT_DRAM:0, NOT_ALLOCATED:17750136, Ratio_DRAM:0.47
DRAM:16711649, NOT_DRAM:0, NOT_ALLOCATED:16534650, Ratio_DRAM:0.50
DRAM:17921360, NOT_DRAM:0, NOT_ALLOCATED:15324939, Ratio_DRAM:0.54
DRAM:22630068, NOT_DRAM:0, NOT_ALLOCATED:10616231, Ratio_DRAM:0.68
DRAM:27805312, NOT_DRAM:0, NOT_ALLOCATED:5440987, Ratio_DRAM:0.84
DRAM:33007760, NOT_DRAM:0, NOT_ALLOCATED:238539, Ratio_DRAM:0.99
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33246299, NOT_DRAM:0, NOT_ALLOCATED:0, Ratio_DRAM:1.00
DRAM:33238846, NOT_DRAM:0, NOT_ALLOCATED:7453, Ratio_DRAM:1.00
DRAM:33237954, NOT_DRAM:0, NOT_ALLOCATED:8345, Ratio_DRAM:1.00
DRAM:33226283, NOT_DRAM:0, NOT_ALLOCATED:20016, Ratio_DRAM:1.00
DRAM:33086301, NOT_DRAM:0, NOT_ALLOCATED:159998, Ratio_DRAM:1.00
DRAM:32946427, NOT_DRAM:0, NOT_ALLOCATED:299872, Ratio_DRAM:0.99
DRAM:32833639, NOT_DRAM:0, NOT_ALLOCATED:412660, Ratio_DRAM:0.99
DRAM:32762516, NOT_DRAM:0, NOT_ALLOCATED:483783, Ratio_DRAM:0.99
DRAM:32755181, NOT_DRAM:0, NOT_ALLOCATED:491118, Ratio_DRAM:0.99
DRAM:32755181, NOT_DRAM:0, NOT_ALLOCATED:491118, Ratio_DRAM:0.99
*/

FILE *g_fp=NULL;
pthread_mutex_t count_mutex;
pthread_t thread_test;
int g_start_check=1;
long g_start_addr;
unsigned long g_obj_size;
int g_running=1;



static void __attribute__((destructor)) exit_lib(void);

void exit_lib(void)
{
    g_running=0;
}


static int
hook(long syscall_number,
			long arg0, long arg1,
			long arg2, long arg3,
			long arg4, long arg5,
			long *result)
{

        int static mmap_id=0;
        struct timespec ts;
        //long int hash;
        char call_stack_concat[SIZE]="";
        //long result;
        static unsigned long g_nodemask;

	if (syscall_number == SYS_mmap) {

		/* pass it on to the kernel */
		*result = syscall_no_intercept(syscall_number, arg0, arg1, arg2, arg3, arg4, arg5);

		pthread_mutex_lock(&count_mutex);
		clock_gettime(CLOCK_MONOTONIC, &ts);

		fprintf(stderr, "%ld.%ld,mmap, %ld, %p\n",ts.tv_sec,ts.tv_nsec,arg1,(void *)*result);
		pthread_mutex_unlock(&count_mutex);


                if(arg1 > 10e10){
    		    size_t pagesize = getpagesize();
		    unsigned long page_count =  (unsigned long)arg1 / pagesize;
                    g_nodemask = 1;
                    unsigned long size = (page_count/2) * pagesize;
                    if(mbind((void *)*result, size, MPOL_BIND, &g_nodemask, 64, MPOL_MF_MOVE) == -1)
                    {
                        fprintf(stderr,"Error:%d\n",errno);
                        perror("Error description");
                    }
                    g_nodemask = 4;
                    if(mbind((void *)*result + (page_count/2) * pagesize, size, MPOL_BIND, &g_nodemask, 64, MPOL_MF_MOVE) == -1)
                    {
                        fprintf(stderr,"Error:%d\n",errno);
                        perror("Error description");
                    }

                    g_start_check=0;
                    g_start_addr = *result;
                    g_obj_size = (unsigned long)arg1;

                }else{
                    g_nodemask = 1;
		    if(mbind((void *)*result, (unsigned long)arg1, MPOL_BIND, &g_nodemask, 64, MPOL_MF_MOVE) == -1)
        	    {
                	fprintf(stderr,"Error:%d\n",errno);
                	perror("Error description");
        	    }
                }


		return 0;
	}else if(syscall_number == SYS_munmap){
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

void *thread_check_mbind(void * _args)
{

        int num_nodes_available = numa_max_node() + 1;
	while(g_start_check){
             sleep(1);
	}

        while(g_running){
            size_t pagesize = getpagesize();
	    unsigned long page_count = g_obj_size / pagesize;
	    void **pages_addr;
	    int *status;
            int i;

	    pages_addr = malloc(sizeof(char *) * page_count);
	    status = malloc(sizeof(int *) * page_count);

	    if (!pages_addr || !status) {
	       fprintf(stderr, "Unable to allocate memory\n");
	       exit(1);
	    }

	    for (int i = 0; i < page_count; i++) {
	        pages_addr[i] = (void *) g_start_addr + i * pagesize;
	        status[i] = -1;
	    }

	    if (numa_move_pages(getpid(), page_count, pages_addr, NULL, status, MPOL_MF_MOVE) == -1) {
	        fprintf(stderr, "[numa_move_pages] error code: %d\n", errno);
	        perror("error description:");
	    }

            int pages_dram=0;
            int pages_unlocated=0;
            int pages_not_dram=0;

	    for (i = 0; i < page_count/2; i++) {
	        if(status[i] >= 0 && status[i] < num_nodes_available){
                   if(status[i] != 0){
                      pages_not_dram++;
                   }else{
		      pages_dram++;
                   }
	        }else{
                   pages_unlocated++;
                }
	    }
            fprintf(stderr,"DRAM:%d, NOT_DRAM:%d, NOT_ALLOCATED:%d, Ratio_DRAM:%.2lf\n", \
                            pages_dram, \
                            pages_not_dram, \
                            pages_unlocated, \
                            (float)pages_dram/(page_count/2));
            sleep(10);
        }
}


static __attribute__((constructor)) void
init(int argc, char * argv[])
{
	setvbuf(stdout, NULL, _IONBF, 0);  //avoid buffer from printf
	intercept_hook_point = hook;
    pthread_create(&thread_test, NULL, thread_check_mbind, NULL);
}