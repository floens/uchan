TEXT = """
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut
labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""

BOARD = 'test'
REPLIES = 300

NAME = 'Name'
SUBJECT = 'Subject'
PASSWORD = 'password'


def load():
    from uchan.lib.tasks.post_task import PostDetails
    from uchan import g

    i = 0
    while True:

        post_details = PostDetails({}, BOARD, None, TEXT, NAME, SUBJECT, PASSWORD, False, 1)

        board_name, thread_id, post_refno = g.posts_service.handle_post(post_details)
        print('posted! ' + str(i))
        i += 1

        for j in range(REPLIES):
            reply_details = PostDetails({}, BOARD, thread_id, TEXT, NAME, SUBJECT, PASSWORD, False, 1)
            g.posts_service.handle_post(reply_details)
            print('replied! ' + str(j))


def test_size():
    from uchan.lib.tasks.post_task import PostDetails
    from uchan import g

    a_board = g.posts_cache.find_board_cached('test')

    post_details = PostDetails({}, BOARD, None, TEXT, NAME, SUBJECT, PASSWORD, False, 1)
    board_name, thread_id, post_refno = g.posts_service.handle_post(post_details)

    a_thread = g.posts_cache.find_thread_cached(thread_id)
    a_post = a_thread.posts[0]

    for j in range(5):
        a_thread.posts.append(a_post)

    threads = []
    for i in range(15 * 10):
        threads.append(a_thread)

    from uchan.lib.cache.posts_cache import BoardPageCacheProxy
    board_cache = BoardPageCacheProxy(a_board.board, threads).convert()

    ret = g.cache.set('foo', board_cache)
    print(ret)


if __name__ == '__main__':
    load()
