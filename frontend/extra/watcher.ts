import { Thread } from "./thread";
import { PageVisibility } from "./pagevisibility";
import { xhrJsonGet } from "./extra";
import { ThreadView } from "./threadview";

export class Watcher {
  delays = [10, 15, 20, 30, 60, 90, 120, 180, 240, 300, 600];
  endPoint = '/api/thread/';

  boardName: string;
  threadRefno: number;
  thread: Thread;
  threadView: ThreadView;
  statusElements: HTMLElement[];

  xhr: XMLHttpRequest = null;
  error = false;

  timeoutId = -1;
  statusTimeoutId = -1;
  currentDelay = 0;
  targetTime = 0;

  documentTitle: string;
  totalNewPosts = 0;

  constructor(boardName, threadRefno, thread: Thread, threadView: ThreadView, statusElements) {
    this.boardName = boardName;
    this.threadRefno = threadRefno;
    this.thread = thread;
    this.threadView = threadView;
    this.statusElements = statusElements;

    this.documentTitle = document.title;

    thread.observe(this.threadViewUpdated.bind(this));

    document.addEventListener('scroll', (e) => this.onScroll(e), false);
    PageVisibility.addListener((visible) => this.pageVisibilityChanged(visible));

    this.updateTimerState(this.delays[0] * 1000);
    this.updateStatus();
  }

  updateTimerState(delay: number) {
    if (this.timeoutId >= 0) {
      clearTimeout(this.timeoutId);
    }

    this.timeoutId = setTimeout(() => {
      this.timeoutId = -1;
      this.timerFired();
    }, delay);
    this.targetTime = Date.now() + delay;
  }

  timerFired() {
    // console.log('timer fired');
    this.update();
    this.updateStatus();
  }

  forceUpdate() {
    this.currentDelay = 0;
    this.update();
  }

  update() {
    if (this.xhr == null) {
      this.xhr = xhrJsonGet(this.endPoint + this.boardName + '/' + this.threadRefno, this.xhrDone.bind(this));
      this.updateStatus();
    }
  }

  resetTimer(newPosts: number) {
    this.totalNewPosts += newPosts;
    let delay;
    if (newPosts == 0) {
      delay = this.delays[this.currentDelay];
      if (this.currentDelay < this.delays.length - 1) {
        this.currentDelay++;
      }
    } else {
      delay = this.delays[0];
      this.currentDelay = 0;
    }

    if (!PageVisibility.isVisible()) {
      delay = Math.max(60, delay);
    }
    this.updateTimerState(delay * 1000);
  }

  pageVisibilityChanged(visible: boolean) {
    if (visible) {
      this.updateStatus();
    }
  }

  afterPost() {
    this.forceUpdate()
  }

  addUpdateListener(element: Element) {
    element.addEventListener('click', (event: Event) => {
      event.preventDefault();
      this.forceUpdate();
    });
  }

  onScroll(event: Event) {
    if (window.innerHeight + window.pageYOffset + 1 > document.documentElement.scrollHeight) {
      this.totalNewPosts = 0;
      this.updateStatus();
    }
  }

  updateStatus() {
    let invalidate = false;

    let status = '';
    if (this.error) {
      status = 'Error';
    } else if (this.xhr != null) {
      status = 'Updating...'
    } else if (this.totalNewPosts > 0) {
      status = this.totalNewPosts + ' new post' + (this.totalNewPosts != 1 ? 's' : '');
    } else {
      status = Math.ceil((this.targetTime - Date.now()) / 1000).toString();
      invalidate = true;
    }
    for (let i = 0; i < this.statusElements.length; i++) {
      this.statusElements[i].textContent = status;
    }

    let newTitle;
    if (this.totalNewPosts > 0) {
      newTitle = '(' + this.totalNewPosts + ') ' + this.documentTitle;
    } else {
      newTitle = this.documentTitle;
    }
    if (newTitle !== document.title) {
      document.title = newTitle;
    }

    if (PageVisibility.isVisible() && invalidate) {
      if (this.statusTimeoutId >= 0) {
        clearTimeout(this.statusTimeoutId);
      }

      this.statusTimeoutId = setTimeout(() => {
        // console.log('update status timer fired');
        this.updateStatus();
      }, 1000);
    }
  }

  xhrDone(error: Error, data: any) {
    if (error) {
      console.error('watcher error', error);
      this.error = true;
    } else {
      this.error = false;
      let previousLength = this.thread.posts.length;
      let thread = data.thread;

      this.thread.update(thread);

      this.resetTimer(this.thread.posts.length - previousLength);
    }

    this.xhr = null;
    this.updateStatus();
  }

  threadViewUpdated(threadView: Thread) {
  }
}
