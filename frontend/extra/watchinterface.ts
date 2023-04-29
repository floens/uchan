import { Persistable, Persistence } from "./persistence";
import { context } from "./extra";

export class Watch implements Persistable {
  board: string;
  thread: number;

  static fromBoardThread(board, thread) {
    let watch = new Watch();
    watch.board = board;
    watch.thread = thread;
    return watch;
  }

  fromObject(obj) {
    this.board = obj['board'];
    this.thread = obj['thread'];
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

    this.element = document.createElement('div');
    this.element.className = 'bookmarks';
    this.element.style.display = 'none';
    this.element.innerHTML = '' +
      '<div class="bookmarks-title">bookmarks</div>' +
      '<ul class="bookmarks-list"></ul>';
    this.bookmarksListElement = <HTMLUListElement>this.element.querySelector('.bookmarks-list');

    let linkListRight = document.querySelector('.link-list-right');
    linkListRight.insertBefore(this.element, linkListRight.firstChild);

    this.openWatchesElement.addEventListener('click', (e) => {
      e.preventDefault();
      this.toggleOpen()
    });

    this.load();
    this.persistence.addCallback('watches', () => {
      this.load();
    });
  }

  watchThis() {
    let boardName = context.boardName;
    let threadRefno = context.threadRefno;

    let watch = Watch.fromBoardThread(boardName, threadRefno);

    for (let i = 0; i < this.watches.length; i++) {
      if (this.watches[i].equals(watch)) {
        return;
      }
    }

    this.addWatch(watch);
  }

  private addWatch(watch: Watch) {
    this.watches.push(watch);
    this.save();
    this.updateView();
  }

  private removeWatch(watch: Watch) {
    for (let i = 0; i < this.watches.length; i++) {
      if (this.watches[i].equals(watch)) {
        this.watches.splice(i, 1);
        break;
      }
    }

    this.save();
    this.updateView();
  }

  private load() {
    this.watches = <Watch[]>this.persistence.retrieveList('watches', Watch);
    this.updateView();
  }

  private save() {
    this.persistence.persistList('watches', this.watches);
  }

  private toggleOpen() {
    this.shown = !this.shown;
    this.element.style.display = this.shown ? 'block' : 'none';
  }

  private deleteClicked(watch) {
    this.removeWatch(watch);
  }

  private updateView() {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    let self = this;
    this.bookmarksListElement.innerHTML = '';
    let frag = document.createDocumentFragment();

    for (let i = 0; i < this.watches.length; i++) {
      let watch = this.watches[i];
      let liElement = document.createElement('li');

      let bookmarkDeleteElement = document.createElement('div');
      bookmarkDeleteElement.className = 'bookmark-delete';
      bookmarkDeleteElement.textContent = '\u2716';

      let spaceElement = document.createTextNode(' ');

      let linkElement = document.createElement('a');
      linkElement.setAttribute('href', '/' + watch.board + '/read/' + watch.thread);
      linkElement.textContent = '/' + watch.board + '/ \u2013 ' + watch.thread;

      liElement.appendChild(bookmarkDeleteElement);
      liElement.appendChild(spaceElement);
      liElement.appendChild(linkElement);

      (function () {
        let i = watch;
        bookmarkDeleteElement.addEventListener('click', () => {
          self.deleteClicked(i);
        });
      })();

      frag.appendChild(liElement);
    }
    this.bookmarksListElement.appendChild(frag);
  }
}
