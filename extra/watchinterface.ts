namespace uchan {
    export class WatchInterface {
        persistence: Persistence;
        openWatchesElement: HTMLElement;

        element: HTMLElement;
        bookmarksListElement: HTMLUListElement;

        constructor(persistence, openWatchesElement) {
            this.persistence = persistence;
            this.openWatchesElement = openWatchesElement;
            this.openWatchesElement.addEventListener('click', (e) => this.openWatches(e));

            this.element = document.createElement('div');
            this.element.className = 'bookmarks';
            this.element.innerHTML = '' +
                '<div class="bookmarks-title">Bookmarks</div>' +
                '<ul class="bookmarks-list"></ul>';
            this.bookmarksListElement = <HTMLUListElement>this.element.querySelector('.bookmarks-list');

            var linkListRight = document.querySelector('.link-list-right');
            linkListRight.insertBefore(this.element, linkListRight.firstChild);

            this.persistence.addCallback('watches', () => {
                this.update();
            });
            this.update();
        }

        openWatches(event) {
            event.preventDefault();
        }

        private update() {
            var self = this;
            this.bookmarksListElement.innerHTML = '';
            var frag = document.createDocumentFragment();
            var watches = this.persistence.getWatches();
            for (var i = 0; i < watches.length; i++) {
                var watch = watches[i];
                var liElement = document.createElement('li');
                liElement.innerHTML = '<li><div class="bookmark-delete">&#x2716;</div> <a href="#">foo</a></li>';
                var del = <HTMLElement>liElement.querySelector('.bookmark-delete');
                (function() {
                    var i = watch;
                    del.addEventListener('click', () => {
                        self.deleteClicked(i);
                    });
                })();
                var anchor = <HTMLElement>liElement.querySelector('a');
                anchor.innerText = watch.board + ' - ' + watch.thread;
                frag.appendChild(liElement);
            }
            this.bookmarksListElement.appendChild(frag);
        }

        private deleteClicked(watch) {
            this.persistence.deleteWatch(watch);
        }
    }
}
