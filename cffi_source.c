/*
 * Copyright (C) 2016, Maximilian Koehl <mail@koehlma.de>
 *
 * This program is free software: you can redistribute it and/or modify it under
 * the terms of the GNU Lesser General Public License version 3 as published by
 * the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
 * PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include <uv.h>

const char* PYTHON_UV_CFFI_VERSION = "__version__";


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
int cross_uv_tcp_open(uv_tcp_t* tcp, int fd) {
    return uv_tcp_open(tcp, (uv_os_sock_t) fd);
}
int cross_uv_udp_open(uv_udp_t* udp, int fd) {
    return uv_udp_open(udp, (uv_os_sock_t) fd);
}


void cross_set_process_uid_gid(uv_process_options_t* options, int uid, int gid) {
    options->uid = (uv_uid_t) uid;
    options->gid = (uv_gid_t) gid;
}

int cross_uv_fs_close(uv_loop_t* loop, uv_fs_t* request, int fd, uv_fs_cb callback) {
    return uv_fs_close(loop, request, (uv_file) fd, callback);
}

void cross_uv_buf_set(uv_buf_t* buffer, char* base, unsigned int length) {
    buffer->base = base;
    buffer->len = length;
}
char* cross_uv_buf_get_base(uv_buf_t* buffer) {
    return buffer->base;
}