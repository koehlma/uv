# -*- coding: utf-8 -*-
#
# Copyright (C) 2015, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__version__ = '0.0.3.dev1'
__project__ = 'Python LibUV CFFI Bindings'
__author__ = 'Maximilian Köhl'
__email__ = 'mail@koehlma.de'

import cffi

declarations = '''
struct addrinfo {
    int     ai_flags;
    int     ai_family;
    int     ai_socktype;
    int     ai_protocol;
    char    *ai_canonname;
    struct  sockaddr *ai_addr;
    struct  addrinfo *ai_next;
    ...;
};

struct sockaddr {
    unsigned short sa_family;
    ...;
};
struct sockaddr_in {
    unsigned short sin_port;
    ...;
};
struct sockaddr_in6 {
    unsigned short sin6_port;
    ...;
};


typedef union {...;} uv_file;
typedef union {...;} uv_os_sock_t;
typedef union {...;} uv_os_fd_t;
typedef union {...;} uv_uid_t;
typedef union {...;} uv_gid_t;


typedef struct {
    long tv_sec;
    long tv_nsec;
} uv_timespec_t;

typedef struct {
    uint64_t st_dev;
    uint64_t st_mode;
    uint64_t st_nlink;
    uint64_t st_uid;
    uint64_t st_gid;
    uint64_t st_rdev;
    uint64_t st_ino;
    uint64_t st_size;
    uint64_t st_blksize;
    uint64_t st_blocks;
    uint64_t st_flags;
    uint64_t st_gen;
    uv_timespec_t st_atim;
    uv_timespec_t st_mtim;
    uv_timespec_t st_ctim;
    uv_timespec_t st_birthtim;
} uv_stat_t;


typedef struct {void* data; ...;} uv_loop_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_handle_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_timer_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_prepare_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_check_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_idle_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_async_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_poll_t;
typedef struct {void* data; uv_loop_t* loop; int signum; ...;} uv_signal_t;
typedef struct {void* data; uv_loop_t* loop; int pid; ...;} uv_process_t;
typedef struct {void* data; uv_loop_t* loop; size_t write_queue_size; ...;} uv_stream_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_tcp_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_pipe_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_tty_t;
typedef struct {void* data; uv_loop_t* loop; size_t send_queue_size; size_t send_queue_count; ...;} uv_udp_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_fs_event_t;
typedef struct {void* data; uv_loop_t* loop; ...;} uv_fs_poll_t;


typedef struct {
    char* base;
    size_t len;
    ...;
} uv_buf_t;

typedef void (*uv_alloc_cb)(uv_handle_t*, size_t, uv_buf_t*);


typedef enum {
    UV_UNKNOWN_HANDLE = 0,
    UV_ASYNC,
    UV_CHECK,
    UV_FS_EVENT,
    UV_FS_POLL,
    UV_HANDLE,
    UV_IDLE,
    UV_NAMED_PIPE,
    UV_POLL,
    UV_PREPARE,
    UV_PROCESS,
    UV_STREAM,
    UV_TCP,
    UV_TIMER,
    UV_TTY,
    UV_UDP,
    UV_SIGNAL,
    UV_FILE,
    UV_HANDLE_TYPE_MAX
} uv_handle_type;


/* Version */
unsigned int uv_version();
const char* uv_version_string();

/* Loop */
typedef enum {
    UV_RUN_DEFAULT = 0,
    UV_RUN_ONCE,
    UV_RUN_NOWAIT
} uv_run_mode;

typedef enum {
    UV_LOOP_BLOCK_SIGNAL
} uv_loop_option;

typedef void (*uv_walk_cb)(uv_handle_t*, void*);

int uv_loop_init(uv_loop_t*);
int uv_loop_configure(uv_loop_t*, uv_loop_option, ...);
int uv_loop_close(uv_loop_t*);
int uv_loop_alive(uv_loop_t*);

uv_loop_t* uv_default_loop();

int uv_run(uv_loop_t*, uv_run_mode);
void uv_stop(uv_loop_t*);

void uv_walk(uv_loop_t*, uv_walk_cb, void*);

uint64_t uv_now(const uv_loop_t*);
void uv_update_time(uv_loop_t*);

int uv_backend_fd(const uv_loop_t*);
int uv_backend_timeout(const uv_loop_t*);


/* Request */
typedef enum {
    UV_UNKNOWN_REQ = 0,
    UV_REQ,
    UV_CONNECT,
    UV_WRITE,
    UV_SHUTDOWN,
    UV_UDP_SEND,
    UV_FS,
    UV_WORK,
    UV_GETADDRINFO,
    UV_GETNAMEINFO,
    ...
} uv_req_type;

typedef struct {
    void* data;
    uv_req_type type;
    ...;
} uv_req_t;

int uv_cancel(uv_req_t* request);


/* Handle */
typedef void (*uv_close_cb)(uv_handle_t*);

int uv_is_active(uv_handle_t*);
int uv_is_closing(uv_handle_t*);

void uv_close(uv_handle_t*, uv_close_cb);

int uv_has_ref(uv_handle_t*);
void uv_ref(uv_handle_t*);
void uv_unref(uv_handle_t*);

int uv_fileno(const uv_handle_t*, uv_os_fd_t* fd);

int uv_send_buffer_size(uv_handle_t*, int*);
int uv_recv_buffer_size(uv_handle_t*, int*);


/* Timer */
typedef void (*uv_timer_cb)(uv_timer_t*);

int uv_timer_init(uv_loop_t*, uv_timer_t*);
int uv_timer_start(uv_timer_t*, uv_timer_cb, uint64_t, uint64_t);
int uv_timer_stop(uv_timer_t*);
int uv_timer_again(uv_timer_t*);

uint64_t uv_timer_get_repeat(uv_timer_t*);
void uv_timer_set_repeat(uv_timer_t*, uint64_t);


/* Prepare */
typedef void (*uv_prepare_cb)(uv_prepare_t*);

int uv_prepare_init(uv_loop_t*, uv_prepare_t*);
int uv_prepare_start(uv_prepare_t*, uv_prepare_cb);
int uv_prepare_stop(uv_prepare_t*);


/* Check */
typedef void (*uv_check_cb)(uv_check_t*);

int uv_check_init(uv_loop_t*, uv_check_t*);
int uv_check_start(uv_check_t*, uv_check_cb);
int uv_check_stop(uv_check_t*);


/* Idle */
typedef void (*uv_idle_cb)(uv_idle_t*);

int uv_idle_init(uv_loop_t*, uv_idle_t*);
int uv_idle_start(uv_idle_t*, uv_idle_cb);
int uv_idle_stop(uv_idle_t*);


/* Async */
typedef void (*uv_async_cb)(uv_async_t*);

int uv_async_init(uv_loop_t*, uv_async_t*, uv_async_cb);
int uv_async_send(uv_async_t*);


/* Poll */
enum uv_poll_event {
    UV_READABLE = 1,
    UV_WRITABLE = 2
};

typedef void (*uv_poll_cb)(uv_poll_t*, int, int);

int uv_poll_init(uv_loop_t*, uv_poll_t*, int);
int uv_poll_init_socket(uv_loop_t*, uv_poll_t*, uv_os_sock_t);
int uv_poll_start(uv_poll_t*, int, uv_poll_cb);
int uv_poll_stop(uv_poll_t*);


/* Signal */
typedef void (*uv_signal_cb)(uv_signal_t*, int);

int uv_signal_init(uv_loop_t*, uv_signal_t*);
int uv_signal_start(uv_signal_t*, uv_signal_cb, int);
int uv_signal_stop(uv_signal_t*);


/* Process */
typedef void (*uv_exit_cb)(uv_process_t*, int64_t, int);

enum uv_process_flags{
    UV_PROCESS_SETUID = 1,
    UV_PROCESS_SETGID = 2,
    UV_PROCESS_WINDOWS_VERBATIM_ARGUMENTS = 4,
    UV_PROCESS_DETACHED = 8,
    UV_PROCESS_WINDOWS_HIDE = 16
};

typedef enum {
    UV_IGNORE = 0,
    UV_CREATE_PIPE = 1,
    UV_INHERIT_FD = 2,
    UV_INHERIT_STREAM = 4,
    UV_READABLE_PIPE = 16,
    UV_WRITABLE_PIPE = 32
} uv_stdio_flags;

typedef struct {
    uv_stdio_flags flags;
    union {
        uv_stream_t* stream;
        int fd;
    } data;
} uv_stdio_container_t;

typedef struct {
    uv_exit_cb exit_cb;
    const char* file;
    char** args;
    char** env;
    const char* cwd;
    unsigned int flags;
    int stdio_count;
    uv_stdio_container_t* stdio;
    uv_uid_t uid;
    uv_gid_t gid;
} uv_process_options_t;

void uv_disable_stdio_inheritance();

int uv_spawn(uv_loop_t*, uv_process_t*, uv_process_options_t*);
int uv_process_kill(uv_process_t*, int signum);
int uv_kill(int pid, int signum);


/* Stream */
typedef struct {
    void* data;
    uv_stream_t* handle;
    ...;
} uv_connect_t;

typedef struct {
    void* data;
    uv_stream_t* handle;
    ...;
} uv_shutdown_t;

typedef struct {
    void* data;
    uv_stream_t* handle;
    uv_stream_t* send_handle;
    ...;
} uv_write_t;

typedef void (*uv_read_cb)(uv_stream_t*, ssize_t, const uv_buf_t*);
typedef void (*uv_write_cb)(uv_write_t*, int);
typedef void (*uv_connect_cb)(uv_connect_t*, int);
typedef void (*uv_shutdown_cb)(uv_shutdown_t*, int);
typedef void (*uv_connection_cb)(uv_stream_t*, int);

int uv_shutdown(uv_shutdown_t*, uv_stream_t*, uv_shutdown_cb);
int uv_listen(uv_stream_t*, int, uv_connection_cb);
int uv_accept(uv_stream_t*, uv_stream_t*);
int uv_read_start(uv_stream_t*, uv_alloc_cb, uv_read_cb);
int uv_read_stop(uv_stream_t*);
int uv_write(uv_write_t*, uv_stream_t*, uv_buf_t[], unsigned int, uv_write_cb);
int uv_write2(uv_write_t*, uv_stream_t*, uv_buf_t[], unsigned int, uv_stream_t*, uv_write_cb);
int uv_try_write(uv_stream_t*, uv_buf_t[], unsigned int);
int uv_is_readable(uv_stream_t*);
int uv_is_writable(uv_stream_t*);
int uv_stream_set_blocking(uv_stream_t*, int);


/* TCP */
enum uv_tcp_flags {
    UV_TCP_IPV6ONLY = 1
};

int uv_tcp_init(uv_loop_t*, uv_tcp_t*);
int uv_tcp_init_ex(uv_loop_t*, uv_tcp_t*, unsigned int);
int uv_tcp_open(uv_tcp_t*, uv_os_sock_t);
int uv_tcp_nodelay(uv_tcp_t*, int);
int uv_tcp_keepalive(uv_tcp_t*, int, unsigned int);
int uv_tcp_simultaneous_accepts(uv_tcp_t*, int);
int uv_tcp_bind(uv_tcp_t*, const struct sockaddr*, unsigned int);
int uv_tcp_getsockname(uv_tcp_t*, struct sockaddr*, int*);
int uv_tcp_getpeername(uv_tcp_t*, struct sockaddr*, int*);
int uv_tcp_connect(uv_connect_t*, uv_tcp_t*, const struct sockaddr*, uv_connect_cb);


/* Pipe */
int uv_pipe_init(uv_loop_t*, uv_pipe_t*, int);
int uv_pipe_open(uv_pipe_t*, uv_file);
int uv_pipe_bind(uv_pipe_t*, char*);
void uv_pipe_connect(uv_connect_t*, uv_pipe_t*, char*, uv_connect_cb);
int uv_pipe_getsockname(uv_pipe_t*, char*, size_t*);
int uv_pipe_getpeername(uv_pipe_t*, char*, size_t*);
void uv_pipe_pending_instances(uv_pipe_t*, int);
int uv_pipe_pending_count(uv_pipe_t*);
uv_handle_type uv_pipe_pending_type(uv_pipe_t*);


/* TTY */
typedef enum {
    UV_TTY_MODE_NORMAL,
    UV_TTY_MODE_RAW,
    UV_TTY_MODE_IO
} uv_tty_mode_t;

int uv_tty_init(uv_loop_t*, uv_tty_t*, uv_file fd, int);
int uv_tty_set_mode(uv_tty_t*, uv_tty_mode_t);
int uv_tty_reset_mode();
int uv_tty_get_winsize(uv_tty_t*, int*, int*);


/* UDP */
typedef struct {
    void* data;
    uv_udp_t* handle;
    ...;
} uv_udp_send_t;

enum uv_udp_flags {
    UV_UDP_IPV6ONLY = 1,
    UV_UDP_PARTIAL = 2,
    UV_UDP_REUSEADDR = 4
};

typedef enum {
    UV_LEAVE_GROUP = 0,
    UV_JOIN_GROUP = 1
} uv_membership;

typedef void (*uv_udp_send_cb)(uv_udp_send_t*, int);
typedef void (*uv_udp_recv_cb)(uv_udp_t*, ssize_t, const uv_buf_t*, const struct sockaddr*, unsigned);

int uv_udp_init(uv_loop_t*, uv_udp_t*);
int uv_udp_init_ex(uv_loop_t*, uv_udp_t*, unsigned int);
int uv_udp_open(uv_udp_t*, uv_os_sock_t);
int uv_udp_bind(uv_udp_t*, const struct sockaddr*, unsigned int);
int uv_udp_getsockname(const uv_udp_t*, struct sockaddr*, int*);
int uv_udp_set_membership(uv_udp_t*, char*, char*, uv_membership);
int uv_udp_set_multicast_loop(uv_udp_t*, int);
int uv_udp_set_multicast_ttl(uv_udp_t*, int);
int uv_udp_set_multicast_interface(uv_udp_t*, char*);
int uv_udp_set_broadcast(uv_udp_t*, int);
int uv_udp_set_ttl(uv_udp_t*, int);
int uv_udp_send(uv_udp_send_t*, uv_udp_t*, uv_buf_t[], unsigned int, const struct sockaddr*, uv_udp_send_cb);
int uv_udp_try_send(uv_udp_t*, uv_buf_t[], unsigned int, const struct sockaddr*);
int uv_udp_recv_start(uv_udp_t*, uv_alloc_cb, uv_udp_recv_cb);
int uv_udp_recv_stop(uv_udp_t*);


/* FS-Event */
enum uv_fs_event {
    UV_RENAME = 1,
    UV_CHANGE = 2
};

enum uv_fs_event_flags {
    UV_FS_EVENT_WATCH_ENTRY = 1,
    UV_FS_EVENT_STAT = 2,
    UV_FS_EVENT_RECURSIVE = 4
};

typedef void (*uv_fs_event_cb)(uv_fs_event_t*, const char*, int, int);

int uv_fs_event_init(uv_loop_t*, uv_fs_event_t*);
int uv_fs_event_start(uv_fs_event_t*, uv_fs_event_cb, char*, unsigned int);
int uv_fs_event_stop(uv_fs_event_t*);
int uv_fs_event_getpath(uv_fs_event_t*, char*, size_t*);

/* FS-Poll */
typedef void (*uv_fs_poll_cb)(uv_fs_poll_t*, int, const uv_stat_t*, const uv_stat_t*);

int uv_fs_poll_init(uv_loop_t*, uv_fs_poll_t*);
int uv_fs_poll_start(uv_fs_poll_t*, uv_fs_poll_cb, char*, unsigned int);
int uv_fs_poll_stop(uv_fs_poll_t*);
int uv_fs_poll_getpath(uv_fs_poll_t*, char*, size_t*);


/* FS */
typedef enum {
    UV_FS_UNKNOWN = -1,
    UV_FS_CUSTOM,
    UV_FS_OPEN,
    UV_FS_CLOSE,
    UV_FS_READ,
    UV_FS_WRITE,
    UV_FS_SENDFILE,
    UV_FS_STAT,
    UV_FS_LSTAT,
    UV_FS_FSTAT,
    UV_FS_FTRUNCATE,
    UV_FS_UTIME,
    UV_FS_FUTIME,
    UV_FS_ACCESS,
    UV_FS_CHMOD,
    UV_FS_FCHMOD,
    UV_FS_FSYNC,
    UV_FS_FDATASYNC,
    UV_FS_UNLINK,
    UV_FS_RMDIR,
    UV_FS_MKDIR,
    UV_FS_MKDTEMP,
    UV_FS_RENAME,
    UV_FS_SCANDIR,
    UV_FS_LINK,
    UV_FS_SYMLINK,
    UV_FS_READLINK,
    UV_FS_CHOWN,
    UV_FS_FCHOWN
} uv_fs_type;

typedef enum {
    UV_DIRENT_UNKNOWN,
    UV_DIRENT_FILE,
    UV_DIRENT_DIR,
    UV_DIRENT_LINK,
    UV_DIRENT_FIFO,
    UV_DIRENT_SOCKET,
    UV_DIRENT_CHAR,
    UV_DIRENT_BLOCK
} uv_dirent_type_t;

typedef struct {
    const char* name;
    uv_dirent_type_t type;
} uv_dirent_t;

typedef struct {
    void* data;
    uv_loop_t* loop;
    uv_fs_type fs_type;
    const char* path;
    ssize_t result;
    uv_stat_t statbuf;
    void* ptr;
    ...;
} uv_fs_t;

typedef void (*uv_fs_cb)(uv_fs_t*);

void uv_fs_req_cleanup(uv_fs_t*);
int uv_fs_close(uv_loop_t*, uv_fs_t*, uv_file, uv_fs_cb);
int uv_fs_open(uv_loop_t*, uv_fs_t*, const char* path, int flags, int mode, uv_fs_cb);
int uv_fs_read(uv_loop_t*, uv_fs_t*, uv_file, const uv_buf_t[], unsigned int, int64_t, uv_fs_cb);
int uv_fs_unlink(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_write(uv_loop_t*, uv_fs_t*, uv_file, const uv_buf_t[], unsigned int, int64_t, uv_fs_cb);
int uv_fs_mkdir(uv_loop_t*, uv_fs_t*, const char*, int, uv_fs_cb);
int uv_fs_mkdtemp(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_rmdir(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_scandir(uv_loop_t*, uv_fs_t*, const char*, int, uv_fs_cb);
int uv_fs_scandir_next(uv_fs_t*, uv_dirent_t*);
int uv_fs_stat(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_fstat(uv_loop_t*, uv_fs_t*, uv_file, uv_fs_cb);
int uv_fs_lstat(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_rename(uv_loop_t*, uv_fs_t*, const char*, const char*, uv_fs_cb);
int uv_fs_fsync(uv_loop_t*, uv_fs_t*, uv_file, uv_fs_cb);
int uv_fs_fdatasync(uv_loop_t*, uv_fs_t*, uv_file, uv_fs_cb);
int uv_fs_ftruncate(uv_loop_t*, uv_fs_t*, uv_file, int64_t, uv_fs_cb);
int uv_fs_sendfile(uv_loop_t*, uv_fs_t*, uv_file, uv_file, int64_t, size_t, uv_fs_cb);
int uv_fs_access(uv_loop_t*, uv_fs_t*, const char*, int, uv_fs_cb);
int uv_fs_chmod(uv_loop_t*, uv_fs_t*, const char*, int, uv_fs_cb);
int uv_fs_fchmod(uv_loop_t*, uv_fs_t*, uv_file, int, uv_fs_cb);
int uv_fs_utime(uv_loop_t*, uv_fs_t*, const char*, double, double, uv_fs_cb);
int uv_fs_futime(uv_loop_t*, uv_fs_t*, uv_file, double, double, uv_fs_cb);
int uv_fs_link(uv_loop_t*, uv_fs_t*, const char*, const char*, uv_fs_cb);
int uv_fs_symlink(uv_loop_t*, uv_fs_t*, const char*, const char*, int, uv_fs_cb);
int uv_fs_readlink(uv_loop_t*, uv_fs_t*, const char*, uv_fs_cb);
int uv_fs_chown(uv_loop_t*, uv_fs_t*, const char*, uv_uid_t, uv_gid_t, uv_fs_cb);
int uv_fs_fchown(uv_loop_t*, uv_fs_t*, uv_file, uv_uid_t, uv_gid_t, uv_fs_cb);


/* Thread-Pool */
typedef struct {
    void* data;
    uv_loop_t* loop;
    ...;
} uv_work_t;

typedef void (*uv_work_cb)(uv_work_t*);
typedef void (*uv_after_work_cb)(uv_work_t*, int);

int uv_queue_work(uv_loop_t*, uv_work_t*, uv_work_cb, uv_after_work_cb);


/* DNS */
typedef struct {
    void* data;
    uv_loop_t* loop;
    struct addrinfo* addrinfo;
    ...;
} uv_getaddrinfo_t;

typedef struct {
    void* data;
    uv_loop_t* loop;
    char host[];
    char service[];
    ...;
} uv_getnameinfo_t;

typedef void (*uv_getaddrinfo_cb)(uv_getaddrinfo_t*, int, struct addrinfo*);
typedef void (*uv_getnameinfo_cb)(uv_getnameinfo_t*, int, const char*, const char*);

int uv_getaddrinfo(uv_loop_t*, uv_getaddrinfo_t*, uv_getaddrinfo_cb, const char*, const char*, const struct addrinfo*);
void uv_freeaddrinfo(struct addrinfo*);

int uv_getnameinfo(uv_loop_t*, uv_getnameinfo_t*, uv_getnameinfo_cb, const struct sockaddr*, int flags);


/* Misc */
typedef struct {
  long tv_sec;
  long tv_usec;
} uv_timeval_t;

typedef struct {
    uv_timeval_t ru_utime;
    uv_timeval_t ru_stime;
    uint64_t ru_maxrss;
    uint64_t ru_ixrss;
    uint64_t ru_idrss;
    uint64_t ru_isrss;
    uint64_t ru_minflt;
    uint64_t ru_majflt;
    uint64_t ru_nswap;
    uint64_t ru_inblock;
    uint64_t ru_oublock;
    uint64_t ru_msgsnd;
    uint64_t ru_msgrcv;
    uint64_t ru_nsignals;
    uint64_t ru_nvcsw;
    uint64_t ru_nivcsw;
} uv_rusage_t;

typedef struct {
    char* model;
    int speed;
    struct uv_cpu_times_s {
        uint64_t user;
        uint64_t nice;
        uint64_t sys;
        uint64_t idle;
        uint64_t irq;
    } cpu_times;
} uv_cpu_info_t;

typedef struct uv_interface_address_s {
    char* name;
    char phys_addr[6];
    int is_internal;
    ...;
} uv_interface_address_t;

uv_handle_type uv_guess_handle(uv_file);

uv_buf_t uv_buf_init(char*, unsigned int);

char** uv_setup_args(int, char**);

int uv_get_process_title(char*, size_t);
int uv_set_process_title(const char*);

int uv_resident_set_memory(size_t*);
int uv_uptime(double*);
int uv_getrusage(uv_rusage_t*);
int uv_cpu_info(uv_cpu_info_t**, int*);
void uv_free_cpu_info(uv_cpu_info_t*, int);
int uv_interface_addresses(uv_interface_address_t**, int*);
void uv_free_interface_addresses(uv_interface_address_t*, int);
void uv_loadavg(double[3]);

int uv_ip4_addr(const char*, int, struct sockaddr_in*);
int uv_ip6_addr(const char*, int, struct sockaddr_in6*);

int uv_ip4_name(const struct sockaddr_in*, char*, size_t);
int uv_ip6_name(const struct sockaddr_in6*, char*, size_t);

int uv_inet_ntop(int, const void*, char*, size_t);
int uv_inet_pton(int, const char*, void*);

int uv_exepath(char*, size_t*);

uint64_t uv_get_total_memory();
uint64_t uv_hrtime();


/* Errors */
#define UV_E2BIG ...
#define UV_EACCES ...
#define UV_EADDRINUSE ...
#define UV_EADDRNOTAVAIL ...
#define UV_EAFNOSUPPORT ...
#define UV_EAGAIN ...
#define UV_EAI_ADDRFAMILY ...
#define UV_EAI_AGAIN ...
#define UV_EAI_BADFLAGS ...
#define UV_EAI_BADHINTS ...
#define UV_EAI_CANCELED ...
#define UV_EAI_FAIL ...
#define UV_EAI_FAMILY ...
#define UV_EAI_MEMORY ...
#define UV_EAI_NODATA ...
#define UV_EAI_NONAME ...
#define UV_EAI_OVERFLOW ...
#define UV_EAI_PROTOCOL ...
#define UV_EAI_SERVICE ...
#define UV_EAI_SOCKTYPE ...
#define UV_EALREADY ...
#define UV_EBADF ...
#define UV_EBUSY ...
#define UV_ECANCELED ...
#define UV_ECHARSET ...
#define UV_ECONNABORTED ...
#define UV_ECONNREFUSED ...
#define UV_ECONNRESET ...
#define UV_EDESTADDRREQ ...
#define UV_EEXIST ...
#define UV_EFAULT ...
#define UV_EFBIG ...
#define UV_EHOSTUNREACH ...
#define UV_EINTR ...
#define UV_EINVAL ...
#define UV_EIO ...
#define UV_EISCONN ...
#define UV_EISDIR ...
#define UV_ELOOP ...
#define UV_EMFILE ...
#define UV_EMSGSIZE ...
#define UV_ENAMETOOLONG ...
#define UV_ENETDOWN ...
#define UV_ENETUNREACH ...
#define UV_ENFILE ...
#define UV_ENOBUFS ...
#define UV_ENODEV ...
#define UV_ENOENT ...
#define UV_ENOMEM ...
#define UV_ENONET ...
#define UV_ENOPROTOOPT ...
#define UV_ENOSPC ...
#define UV_ENOSYS ...
#define UV_ENOTCONN ...
#define UV_ENOTDIR ...
#define UV_ENOTEMPTY ...
#define UV_ENOTSOCK ...
#define UV_ENOTSUP ...
#define UV_EPERM ...
#define UV_EPIPE ...
#define UV_EPROTO ...
#define UV_EPROTONOSUPPORT ...
#define UV_EPROTOTYPE ...
#define UV_ERANGE ...
#define UV_EROFS ...
#define UV_ESHUTDOWN ...
#define UV_ESPIPE ...
#define UV_ESRCH ...
#define UV_ETIMEDOUT ...
#define UV_ETXTBSY ...
#define UV_EXDEV ...
#define UV_UNKNOWN ...
#define UV_EOF ...
#define UV_ENXIO ...
#define UV_EMLINK ...
#define UV_EHOSTDOWN ...

const char* uv_strerror(int);
const char* uv_err_name(int);


/* Python */
const char* python_cffi_uv_version;

typedef struct {
    void* magic;
    void* object;
} py_data;

void* py_attach(py_data* data, void* object);
py_data* py_detach(void* pointer);

typedef struct {
    void* magic;
    void* object;
    struct {
        char* base;
        size_t length;
        int in_use;
    } buffer;
} py_loop_data;

void* py_loop_attach(py_loop_data* data, void* object);
py_loop_data* py_loop_detach(void* pointer);
void py_allocate(uv_handle_t*, size_t, uv_buf_t*);
void py_release(uv_handle_t*);
uv_alloc_cb py_get_allocator();


/* Cross-Platform */
typedef struct {
    uint64_t flowinfo;
    uint64_t scope_id;
} cross_ipv6_additional;

cross_ipv6_additional cross_get_ipv6_additional(struct sockaddr_in6*);
void cross_set_ipv6_additional(struct sockaddr_in6*, uint64_t, uint64_t);


int cross_uv_poll_init_socket(uv_loop_t*, uv_poll_t*, int);
uv_handle_type cross_uv_guess_handle(int);
int cross_uv_tty_init(uv_loop_t*, uv_tty_t*, int, int);
int cross_uv_pipe_open(uv_pipe_t*, int);
void cross_set_process_uid_gid(uv_process_options_t*, int, int);

int cross_uv_fs_close(uv_loop_t*, uv_fs_t*, int, uv_fs_cb);

'''

source = '''
#include <uv.h>

const char* python_cffi_uv_version = "0.0.3.dev0";


/* Python */
typedef struct {
    void* magic;
    void* object;
} py_data;

void* py_attach(py_data* data, void* object) {
    data->magic = &py_attach;
    data->object = object;
    return (void*) data;
}

py_data* py_detach(void* pointer) {
    if (pointer != NULL && ((py_data*) pointer)->magic == &py_attach) {
        return (py_data*) pointer;
    }
    return NULL;
}


typedef struct {
    void* magic;
    void* object;
    struct {
        char* base;
        size_t length;
        int in_use;
    } buffer;
} py_loop_data;

void* py_loop_attach(py_loop_data* data, void* object) {
    data->magic = py_loop_attach;
    data->object = object;
    return (void*) data;
}

py_loop_data* py_loop_detach(void* pointer) {
    if (pointer != NULL && ((py_loop_data*) pointer)->magic == &py_loop_attach) {
        return (py_loop_data*) pointer;
    }
    return NULL;
}

void py_allocate(uv_handle_t* handle, size_t suggested_size, uv_buf_t* buffer) {
    py_loop_data* data = handle->loop->data;
    if (data->buffer.in_use) {
        buffer->base = NULL;
        buffer->len = 0;
    } else {
        buffer->base = data->buffer.base;
        buffer->len = data->buffer.length;
        data->buffer.in_use = 1;
    }
}

void py_release(uv_handle_t* handle) {
    py_loop_data* data = handle->loop->data;
    data->buffer.in_use = 0;
}

static uv_alloc_cb py_get_allocator(void) {
    return &py_allocate;
}


/* Cross-Platform */
typedef struct {
    uint64_t flowinfo;
    uint64_t scope_id;
} cross_ipv6_additional;

cross_ipv6_additional cross_get_ipv6_additional(struct sockaddr_in6* addr) {
    cross_ipv6_additional result;
    result.flowinfo = (uint64_t) addr->sin6_flowinfo;
    result.scope_id = (uint64_t) addr->sin6_scope_id;
    return result;
}

void cross_set_ipv6_additional(struct sockaddr_in6* addr, uint64_t flowinfo, uint64_t scope_id) {
    addr->sin6_flowinfo = flowinfo;
    addr->sin6_scope_id = scope_id;
}



int cross_uv_poll_init_socket(uv_loop_t* loop, uv_poll_t* poll, int fd) {
    return uv_poll_init_socket(loop, poll, (uv_os_sock_t) fd);
}
uv_handle_type cross_uv_guess_handle(int fd) {
    return uv_guess_handle((uv_file) fd);
}
int cross_uv_tty_init(uv_loop_t* loop, uv_tty_t* tty, int fd, int readable) {
    return uv_tty_init(loop, tty, (uv_file) fd, readable);
}
int cross_uv_pipe_open(uv_pipe_t* pipe, int fd) {
    return uv_pipe_open(pipe, (uv_file) fd);
}
void cross_set_process_uid_gid(uv_process_options_t* options, int uid, int gid) {
    options->uid = (uv_uid_t) uid;
    options->gid = (uv_gid_t) gid;
}

int cross_uv_fs_close(uv_loop_t* loop, uv_fs_t* request, int fd, uv_fs_cb callback) {
    return uv_fs_close(loop, request, (uv_file) fd, callback);
}
'''


try:
    from _uvcffi import ffi, lib
except ImportError:
    ffi = cffi.FFI()
    ffi.cdef(declarations)
    try:
        ffi.set_source('_uvcffi', source, libraries=['uv'])
        ffi.compile()
        from _uvcffi import ffi, lib
    except AttributeError or ImportError:
        lib = ffi.verify(source, libraries=['uv'], modulename='_uvcffi')
