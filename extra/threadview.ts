module uchan {
    export interface ThreadViewCallback {
        onRefnoClicked(post: Post);

        onImageClicked(postView: PostView, file: PostFile, fileContainer: HTMLElement);
    }

    export class ThreadView {
        thread: Thread;

        container: HTMLElement;
        views: PostView[] = [];
        callback: uchan.ThreadViewCallback;

        hoveringPostContainer: HTMLElement;
        hoveringPostView: PostView = null;
        highlightedPostView: PostView = null;

        constructor(container: HTMLElement, thread: Thread, callback: ThreadViewCallback) {
            this.container = container;
            this.thread = thread;
            this.callback = callback;

            this.hoveringPostContainer = document.createElement('div');
            this.hoveringPostContainer.id = 'hovering-post-container';
            this.hoveringPostContainer.style.position = 'relative';
            this.container.insertBefore(this.hoveringPostContainer, this.container.firstChild);

            thread.observe(this.threadUpdated.bind(this));
        }

        bindViews() {
            let posts = this.thread.posts;
            let postElements = <NodeListOf<HTMLElement>>this.container.querySelectorAll('.post');

            for (let i = 0; i < posts.length; i++) {
                let postView = new PostView();
                this.views.push(postView);
                this.bindPostView(postView, posts[i], postElements[i]);
            }
        }

        threadUpdated(thread: Thread) {
            for (let i = this.views.length; i < thread.posts.length; i++) {
                let post = thread.posts[i];
                let postElement = PostView.buildPostElement(post);

                let postView = new PostView();
                this.bindPostView(postView, post, postElement);
                this.views.push(postView);

                this.container.lastElementChild.classList.add('divider');
                this.container.appendChild(postElement);
            }
        }

        bindPostView(postView: PostView, post: Post, postElement: HTMLElement) {
            post.views.push(postView); // TODO
            postView.bind(this, post, postElement);
        }

        refnoClicked(postView: PostView) {
            this.callback.onRefnoClicked(postView.post);
        }

        imageClicked(postView: PostView, file: PostFile, fileContainer: HTMLElement) {
            this.callback.onImageClicked(postView, file, fileContainer);
        }

        quoteHover(quoteElement: HTMLElement, refno: number, mouseIn: boolean) {
            this.highlightOrHoverPostForElement(quoteElement, refno, mouseIn);
        }

        backrefHover(backrefElement: HTMLElement, refno: number, mouseIn: boolean) {
            this.highlightOrHoverPostForElement(backrefElement, refno, mouseIn);
        }

        highlightOrHoverPostForElement(referenceElement: HTMLElement, refno: number, mouseIn: boolean) {
            if (this.hoveringPostView) {
                this.hoveringPostView.element.parentNode.removeChild(this.hoveringPostView.element);
                this.hoveringPostView = null;
            }
            if (this.highlightedPostView) {
                this.highlightedPostView.element.classList.remove('highlight');
                this.highlightedPostView = null;
            }

            if (mouseIn) {
                let post = this.thread.findByRefno(refno);
                if (post) {
                    let highlight = false;
                    let highlightPostView: PostView = null;
                    for (let i = 0; i < post.views.length; i++) {
                        if (post.views[i] instanceof PostView) {
                            let postView = post.views[i];
                            let bb = postView.element.getBoundingClientRect();
                            if (bb.top >= 0 && bb.bottom < document.documentElement.clientHeight) {
                                highlight = true;
                                highlightPostView = postView;
                                break;
                            }
                        }
                    }

                    if (highlight) {
                        highlightPostView.element.classList.add('highlight');
                        this.highlightedPostView = highlightPostView;
                    } else {
                        this.hoveringPostView = new PostView();
                        let element = PostView.buildPostElement(post);
                        element.classList.add('post-hover');
                        this.hoveringPostView.bind(this, post, element);

                        let el = this.hoveringPostView.element;

                        let quoteBB = referenceElement.getBoundingClientRect();
                        let containerBB = this.hoveringPostContainer.getBoundingClientRect();

                        el.style.position = 'absolute';

                        let leftPadding = 12;
                        let left = quoteBB.right - containerBB.left + leftPadding;
                        el.style.left = (left) + 'px';

                        this.hoveringPostContainer.appendChild(this.hoveringPostView.element);
                        let hoverBB = this.hoveringPostView.element.getBoundingClientRect();

                        let top = quoteBB.top + quoteBB.height / 2 - containerBB.top - hoverBB.height / 2;
                        el.style.top = (top) + 'px';

                        /*let viewportHeight = document.documentElement.clientHeight;
                        if (hoverBB.bottom > viewportHeight) {
                            top = quoteBB.top - containerBB.top - hoverBB.height;
                            el.style.top = (top) + 'px';
                        }*/
                    }
                }
            }
        }

        quoteClicked(postView: PostView, quoteElement: HTMLElement, refno: number) {
            let post = this.thread.findByRefno(refno);
            if (post) {
                for (let i = 0; i < post.views.length; i++) {
                    if (post.views[i] instanceof PostView) {
                        let postView = post.views[i];
                        console.log(postView.element);
                        postView.element.scrollIntoView();
                    }
                }
            }
        }
    }

    export class PostView {
        threadView: ThreadView;
        post: uchan.Post;

        element: HTMLElement;
        refnoElement: HTMLElement;
        fileElements: NodeListOf<HTMLElement>;
        quotes: NodeListOf<HTMLElement>;
        backrefContainer: HTMLElement;
        backrefs: HTMLElement[] = [];

        boundPostUpdated: (post: Post) => void;
        boundRefnoClicked: (event: Event) => void;
        boundImageClicked: (event: Event) => void;
        boundQuoteEvent: (event: Event) => void;
        boundBackrefEvent: (event: Event) => void;

        bind(threadView: ThreadView, fromPost: Post, element: HTMLElement) {
            this.threadView = threadView;
            this.post = fromPost;
            this.element = element;
            this.refnoElement = <HTMLElement> element.querySelector('a.refno');
            this.fileElements = <NodeListOf<HTMLElement>>element.querySelectorAll('.post .file');
            this.quotes = <NodeListOf<HTMLElement>>element.querySelectorAll('.text a.rquote');

            this.backrefContainer = document.createElement('span');
            this.backrefContainer.classList.add('backref-container');
            let headerElement = this.element.querySelector('.header');
            headerElement.insertBefore(this.backrefContainer, headerElement.lastChild);

            this.boundPostUpdated = this.postUpdated.bind(this);
            this.boundRefnoClicked = this.refnoClicked.bind(this);
            this.boundImageClicked = this.imageClicked.bind(this);
            this.boundQuoteEvent = this.quoteEvent.bind(this);
            this.boundBackrefEvent = this.backrefEvent.bind(this);

            this.post.observe(this.boundPostUpdated);
            this.postUpdated(this.post);
        }

        postUpdated(post: Post) {
            let refno = this.refnoElement;

            refno.removeEventListener('click', this.boundRefnoClicked);
            refno.addEventListener('click', this.boundRefnoClicked);

            for (let i = 0; i < this.fileElements.length; i++) {
                let fileContainer = this.fileElements[i];
                let image = <HTMLImageElement>fileContainer.querySelector('img');
                image.removeEventListener('click', this.boundImageClicked);
                image.addEventListener('click', this.boundImageClicked);
            }

            for (let i = 0; i < this.quotes.length; i++) {
                let quote = this.quotes[i];

                quote.removeEventListener('mouseover', this.boundQuoteEvent);
                quote.removeEventListener('mouseout', this.boundQuoteEvent);
                quote.removeEventListener('click', this.boundQuoteEvent);
                quote.addEventListener('mouseover', this.boundQuoteEvent);
                quote.addEventListener('mouseout', this.boundQuoteEvent);
                quote.addEventListener('click', this.boundQuoteEvent);
            }

            this.backrefContainer.innerHTML = '';
            for (let i = 0; i < this.post.referencedBy.length; i++) {
                let ref = this.post.referencedBy[i];
                let refElement = document.createElement('a');
                refElement.classList.add('backref');
                refElement.textContent = '>>' + ref;
                refElement.setAttribute('href', '#p' + ref);
                refElement.addEventListener('mouseover', this.boundBackrefEvent);
                refElement.addEventListener('mouseout', this.boundBackrefEvent);
                this.backrefs.push(refElement);
                this.backrefContainer.appendChild(refElement);
                this.backrefContainer.appendChild(document.createTextNode(' '));
            }
        }

        refnoClicked(event: Event) {
            event.preventDefault();
            this.threadView.refnoClicked(this);
        }

        imageClicked(event: MouseEvent) {
            if (event.button == 0 && !event.shiftKey && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();

                for (let i = 0; i < this.fileElements.length; i++) {
                    let fileContainer = this.fileElements[i];
                    let image = <HTMLImageElement>fileContainer.querySelector('img');
                    if (image === event.target) {
                        this.threadView.imageClicked(this, this.post.files[i], fileContainer);
                    }
                }
            }
        }

        quoteEvent(event: Event) {
            let quoteElement = <HTMLElement>event.target;
            let refno = parseInt(quoteElement.textContent.substr(2));

            if (event.type == 'mouseover') {
                this.threadView.quoteHover(quoteElement, refno, true);
            } else if (event.type == 'mouseout') {
                this.threadView.quoteHover(quoteElement, refno, false);
            } else if (event.type == 'click') {
                this.threadView.quoteClicked(this, quoteElement, refno);
            }
        }

        backrefEvent(event: Event) {
            let backrefElement = <HTMLElement>event.target;
            let refno = parseInt(backrefElement.textContent.substr(2));

            if (event.type == 'mouseover') {
                this.threadView.backrefHover(backrefElement, refno, true);
            } else if (event.type == 'mouseout') {
                this.threadView.backrefHover(backrefElement, refno, false);
            }
        }

        static buildPostElement(post: Post) {
            let postDiv = document.createElement('div');
            postDiv.className = 'post';
            postDiv.id = 'p#' + post.refno;

            let postHtml = '<div class="header">';

            let files = post.files || [];

            if (post.subject) {
                postHtml += '<span class="subject">' + escape(post.subject) + '</span><br>';
            }

            postHtml += '<a href="#p' + post.refno + '" class="refno">#' + post.refno + '</a> ' +
                '<span class="name">' + PostView.getPostNameHtml(post.name) + '</span> ';

            if (post.modCode) {
                postHtml += '<span class="modcode">' + escape(post.modCode) + '</span> ';
            }

            postHtml += '<span class="date">' + PostView.getPostDateText(post.date) + '</span> ' +
                '<span class="manage"><input type="checkbox" name="post_id" value="' + post.id + '"></span>';

            for (let i = 0; i < files.length; i++) {
                if (i == 0) {
                    postHtml += '<br>';
                }

                let file = files[i];
                postHtml += 'File: <a href="' + escape(file.location) + '">' + escape(file.name) + '</a> ';
                postHtml += '(' + PostView.getPostFileSizeText(file.size) + ', ' + file.width + 'x' + file.height + ')';
                if (i < files.length - 1) {
                    postHtml += '<br>';
                }
            }

            postHtml += '</div>\n';

            if (post.html) {
                postHtml += '<div class="text styled-text">' + post.html + '</div>';
            }

            for (let i = 0; i < files.length; i++) {
                let file = files[i];
                postHtml += '<div class="file">';
                postHtml += '<a class="file-link" href="' + escape(file.location) + '" data-filewidth="' + file.width + '" data-fileheight="' + file.height + '" data-filename="' + escape(file.name) + '" data-filesize="' + file.size + '">';
                postHtml += '<img src="' + escape(file.thumbnailLocation) + '" width="' + file.thumbnailWidth + '" height="' + file.thumbnailHeight + '">';
                postHtml += '</a>';
                postHtml += '</div> ';
            }

            postDiv.innerHTML = postHtml;

            return postDiv;
        }

        static getPostNameHtml(name: string) {
            let html = escape(name);
            let i = html.indexOf('!');
            if (i >= 0) {
                html = html.substring(0, i) + '<span class="trip">!' + html.substring(i + 1) + '</span>';
            }
            return html;
        }

        static getPostFileSizeText(bytes: number) {
            let prefixes = ['kB', 'MB', 'GB', 'TB'];
            if (bytes == 1) {
                return '1 Byte'
            } else if (bytes < 1000) {
                return bytes + ' Bytes';
            } else {
                for (let i = 0; i < prefixes.length; i++) {
                    let unit = Math.pow(1000, i + 2);
                    if (bytes < unit) {
                        return round((1000 * bytes / unit), 1) + ' ' + prefixes[i];
                    }
                }
            }
        }

        static getPostDateText(postDate: number) {
            let date = new Date(postDate);

            // %Y-%m-%d %H:%M:%S
            let output = date.getUTCFullYear() + '-' + lpad(date.getUTCMonth() + 1, 2, '0') + '-' + lpad(date.getUTCDate(), 2, '0') + ' ';
            output += lpad(date.getUTCHours(), 2, '0') + ':' + lpad(date.getUTCMinutes(), 2, '0') + ':' + lpad(date.getUTCSeconds(), 2, '0');
            return output;
        }
    }
}
