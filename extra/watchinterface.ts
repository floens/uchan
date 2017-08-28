/// <reference path="extra.ts" />

namespace uchan {
    export class Watch {
        board: string;
        thread: number;

        static fromBoardThread(board, thread) {
            let watch = new Watch();
            watch.board = board;
            watch.thread = thread;
            return watch;
        }

        static fromObject(obj) {
            let watch = new Watch();
            watch.board = obj['board'];
            watch.thread = obj['thread'];
            return watch;
        }

        toObject() {
            return {
                'board': this.board,
                'thread': this.thread
            }
        }

        equals(other: Watch) {
            return this.board === other.board && this.thread === other.thread;
        }
    }

    export class WatchInterface {
        persistence: Persistence;

        watches: Watch[];

        openWatchesElement: HTMLElement;
        shown = false;

        element: HTMLElement;
        bookmarksListElement: HTMLUListElement;

        constructor(persistence, openWatchesElement) {
            this.persistence = persistence;
            this.openWatchesElement = openWatchesElement;
            this.openWatchesElement.addEventListener('click', (e) => this.openWatches(e));

            this.element = document.createElement('div');
            this.element.className = 'bookmarks';
            this.element.style.display = 'none';
            this.element.innerHTML = '' +
                '<div class="bookmarks-title">bookmarks</div>' +
                '<ul class="bookmarks-list"></ul>';
            this.bookmarksListElement = <HTMLUListElement>this.element.querySelector('.bookmarks-list');

            let linkListRight = document.querySelector('.link-list-right');
            linkListRight.insertBefore(this.element, linkListRight.firstChild);

            this.persistence.addCallback('watches', () => {
                this.update();
            });
            this.update();
        }

        openWatches(event) {
            event.preventDefault();
            this.shown = !this.shown;
            this.element.style.display = this.shown ? 'block' : 'none';
        }

        watchThis() {
            let boardName = uchan.context.boardName;
            let threadRefno = uchan.context.threadRefno;

            let watch = Watch.fromBoardThread(boardName, threadRefno);

            for (let i = 0; i < this.watches.length; i++) {
                if (this.watches[i].equals(watch)) {
                    return;
                }
            }

            context.persistence.addWatch(watch);
        }

        private update() {
            let self = this;
            this.bookmarksListElement.innerHTML = '';
            let frag = document.createDocumentFragment();
            this.watches = this.persistence.getWatches();
            for (let i = 0; i < this.watches.length; i++) {
                let watch = this.watches[i];
                let liElement = document.createElement('li');

                let bookmarkDeleteElement = document.createElement('div');
                bookmarkDeleteElement.className = 'bookmark-delete';
                bookmarkDeleteElement.textContent = '\u2716';

                let spaceElement = document.createTextNode(' ');

                let linkElement = document.createElement('a');
                linkElement.setAttribute('href', '/' + watch.board + '/read/' + watch.thread);

                liElement.appendChild(bookmarkDeleteElement);
                liElement.appendChild(spaceElement);
                liElement.appendChild(linkElement);

                (function () {
                    let i = watch;
                    bookmarkDeleteElement.addEventListener('click', () => {
                        self.deleteClicked(i);
                    });
                })();
                let anchor = <HTMLElement>liElement.querySelector('a');

                let text = '/' + watch.board + '/ \u2013 ' + watch.thread;
                anchor.innerText = escape(text);
                frag.appendChild(liElement);
            }
            this.bookmarksListElement.appendChild(frag);
        }

        private deleteClicked(watch) {
            this.persistence.deleteWatch(watch);
        }
    }
}
