/// <reference path="qr.ts" />
/// <reference path="imageexpansion.ts" />
/// <reference path="watcher.ts" />
/// <reference path="watchinterface.ts" />
/// <reference path="persistence.ts" />

module uchan {
    export var context = {
        mode: null as string,
        boardName: null as string,
        postEndpoint: null as string,
        filePostingEnabled: false,
        threadRefno: null as number,
        locked: false,
        sticky: false,

        persistence: null as Persistence,
        qr: null as QR
    };

    export var escape = function(text) {
        text = text.toString();
        text = text.replace('&', '&amp;');
        text = text.replace('>', '&gt;');
        text = text.replace('<', '&lt;');
        text = text.replace("'", '&#39;');
        text = text.replace('"', '&#34;');
        return text;
    };

    export var lpad = function(str, len, fill) {
        str = str.toString();
        while (str.length < len) {
            str = fill + str;
        }
        return str;
    };

    export var round = function(num, digits) {
        var i = Math.pow(10, digits);
        return Math.round(num * i) / i;
    };

    export var xhrJsonGet = function(endpoint: string, callback: (error: Error, data: any) => void) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', endpoint);
        xhr.send(null);
        xhr.onload = function(event) {
            if (xhr.status == 200) {
                var jsonData = null;
                var e: Error = null;
                try {
                    jsonData = JSON.parse(xhr.responseText);
                } catch (err) {
                    e = err;
                }

                if (jsonData != null) {
                    callback(null, jsonData);
                } else {
                    callback(e, null);
                }
            } else {
                xhr.onerror(event);
            }
        };
        xhr.onerror = function(event) {
            callback(new Error(event.type), null);
        };
        return xhr;
    };

    var init = function() {
        var pageDetails = window['pageDetails'];
        if (!pageDetails) {
            console.error('window.pageDetails not defined');
        } else {
            context.mode = pageDetails.mode;
            context.boardName = pageDetails.boardName;
            context.postEndpoint = pageDetails.postEndpoint;
            context.filePostingEnabled = pageDetails.filePostingEnabled || false;
            context.threadRefno = pageDetails.threadRefno || null;
            context.locked = pageDetails.locked || false;
            context.sticky = pageDetails.sticky || false;

            context.persistence = new Persistence();

            var linkListRight = document.querySelector('.top-bar-right');
            linkListRight.innerHTML = '[<a id="open-watches" href="#">Bookmarks</a>] ' + linkListRight.innerHTML;
            var openWatches = linkListRight.querySelector('#open-watches');

            var watchInterface = new WatchInterface(context.persistence, openWatches);

            var threadControls = document.querySelectorAll('.thread-controls');
            var openQrControls: HTMLElement[] = [];
            var watchThreadControls: HTMLElement[] = [];
            var watchUpdateControls: HTMLElement[] = [];
            var watchStatusElements: HTMLElement[] = [];

            if (context.mode == 'thread') {
                for (var i = 0; i < threadControls.length; i++) {
                    var threadControl = threadControls[i];
                    threadControl.innerHTML += '[<a class="open-qr" href="#">Reply</a>]' +
                        ' [<a class="watch-thread" href="#">Watch thread</a>]' +
                        ' [<a class="watch-update" href="#">Update</a>] <span class="watch-status"></span>';

                    openQrControls.push(<HTMLElement>threadControl.querySelector('.open-qr'));
                    watchThreadControls.push(<HTMLElement>threadControl.querySelector('.watch-thread'));
                    watchUpdateControls.push(<HTMLElement>threadControl.querySelector('.watch-update'));
                    watchStatusElements.push(<HTMLElement>threadControl.querySelector('.watch-status'));
                }

                for (var i = 0; i < watchThreadControls.length; i++) {
                    var watchThreadControl = watchThreadControls[i];
                    watchThreadControl.addEventListener('click', function(e) {
                        e.preventDefault();
                        context.persistence.addWatch(context.boardName, context.threadRefno);
                    });
                }
            }

            if (context.mode == 'board' || context.mode == 'thread') {
                var imageExpansion = new ImageExpansion();
                imageExpansion.bindImages();
            }

            if (context.mode == 'thread' && !context.locked) {
                var postForm = document.querySelector('.post-form');
                //postForm.style.display = 'none';

                var postsElement = document.querySelector('.posts');
                var watcher = new Watcher(context.boardName, context.threadRefno, postsElement, watchStatusElements, imageExpansion);
                var posts = <NodeListOf<HTMLElement>>postsElement.querySelectorAll('.post');
                watcher.bindPosts(posts);

                context.qr = new QR(watcher);
                for (var i = 0; i < openQrControls.length; i++) {
                    context.qr.addShowClickListener(openQrControls[i]);
                }
                for (var i = 0; i < watchUpdateControls.length; i++) {
                    watcher.addUpdateListener(watchUpdateControls[i]);
                }
                watcher.bindRefnos();
            }
        }
    };

    init();
}
