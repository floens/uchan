/// <reference path="imageexpansion.ts" />
/// <reference path="pagevisibility.ts" />

namespace uchan {
    export class Watcher {
        delays = [10, 15, 20, 30, 60, 90, 120, 180, 240, 300];
        endPoint = '/api/thread/';

        threadId:number;
        postsElement:HTMLElement;
        statusElement:HTMLElement;
        imageExpansion:ImageExpansion;

        xhr:XMLHttpRequest = null;
        error = false;
        posts:any[] = [];

        timeoutId = -1;
        statusTimeoutId = -1;
        currentDelay = 0;
        targetTime = 0;

        documentTitle:string;
        totalNewPosts = 0;

        constructor(threadId, postsElement, statusElement, imageExpansion) {
            this.threadId = threadId;
            this.postsElement = postsElement;
            this.statusElement = statusElement;
            this.imageExpansion = imageExpansion;

            this.documentTitle = document.title;

            document.addEventListener('scroll', (e) => this.onScroll(e), false);

            PageVisibility.addListener((visible) => this.pageVisibilityChanged(visible));
            this.updateTimerState(this.delays[0] * 1000);
            this.updateStatus();
        }

        updateTimerState(delay:number) {
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
                this.xhr = xhrJsonGet(this.endPoint + this.threadId, this.xhrDone.bind(this));
                this.updateStatus();
            }
        }

        resetTimer(newPosts:number) {
            this.totalNewPosts += newPosts;
            var delay;
            if (newPosts == 0 && this.currentDelay < this.delays.length - 1) {
                delay = this.delays[this.currentDelay];
                this.currentDelay++;
            } else {
                delay = this.delays[0];
                this.currentDelay = 0;
            }

            if (!PageVisibility.isVisible()) {
                delay = Math.max(60, delay);
            }
            this.updateTimerState(delay * 1000);
        }

        pageVisibilityChanged(visible:boolean) {
            if (visible) {
                this.updateStatus();
            }
        }

        afterPost() {
            setTimeout(() => this.forceUpdate(), 500);
        }

        addUpdateListener(element:Element) {
            element.addEventListener('click', (event:Event) => {
                event.preventDefault();
                this.forceUpdate();
            });
        }

        onScroll(event:Event) {
            if (window.innerHeight + window.pageYOffset + 1 > document.documentElement.scrollHeight) {
                this.totalNewPosts = 0;
                this.updateStatus();
            }
        }

        updateStatus() {
            var invalidate = false;

            var status = '';
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
            this.statusElement.textContent = status;

            if (this.totalNewPosts > 0) {
                document.title = '(' + this.totalNewPosts + ') ' + this.documentTitle;
            } else {
                document.title = this.documentTitle;
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

        xhrDone(error:Error, data:any) {
            if (error) {
                console.error('watcher error');
                this.error = true;
            } else {
                this.error = false;
                var previousLength = this.posts.length;
                var thread = data.thread;
                var remotePosts = thread.posts;
                for (var i = 0; i < remotePosts.length; i++) {
                    var remotePost = remotePosts[i];

                    var has = false;
                    for (var j = 0; j < this.posts.length; j++) {
                        var post = this.posts[j];
                        if (post.id == remotePost.id) {
                            has = true;
                            break;
                        }
                    }

                    if (!has) {
                        this.posts.push(remotePost);
                        var postElement = this.buildPostElement(remotePost);
                        this.postsElement.lastElementChild.classList.add('divider');
                        this.postsElement.appendChild(postElement);
                    }
                }

                this.resetTimer(this.posts.length - previousLength);
            }

            this.xhr = null;
            this.updateStatus();
        }

        buildPostElement(postData:any) {
            var postDiv = document.createElement('div');
            postDiv.className = 'post';
            postDiv.id = 'p#' + postData.refno;

            var postHtml = '<div class="header">';

            var file = postData.file;

            if (postData.subject) {
                postHtml += '<span class="subject">' + escape(postData.subject) + '</span><br>';
            }

            postHtml += '<a href="#p' + postData.refno + '" class="refno">#' + postData.refno + '</a> ' +
                '<span class="name">' + this.getPostNameHtml(postData.name) + '</span> ';

            if (postData.modCode) {
                postHtml += '<span class="modcode">' + escape(postData.modCode) + '</span> ';
            }

            postHtml += '<span class="date">' + this.getPostDateText(postData.date) + '</span> ' +
                '<span class="manage"><input type="checkbox" name="post_id" value="' + postData.id + '"></span>';

            if (file) {
                postHtml += '<br>File: <a href="' + escape(file.location) + '">' + escape(file.name) + '</a> ';
                postHtml += '(' + this.getPostFileSizeText(file.size) + ', ' + file.width + 'x' + file.height + ')';
            }

            postHtml += '</div>\n';

            if (postData.html) {
                postHtml += '<div class="styled-text">' + postData.html + '</div>';
            }

            if (file) {
                postHtml += '<div class="file">';
                postHtml += '<a class="file-link" href="' + escape(file.location) + '" data-filewidth="' + file.width + '" data-fileheight="' + file.height + '" data-filename="' + escape(file.name) + '" data-filesize="' + file.size + '">';
                postHtml += '<img src="' + escape(file.thumbnailLocation) + '" width="' + file.thumbnailWidth + '" height="' + file.thumbnailHeight + '">';
                postHtml += '</a>';
                postHtml += '</div>';
            }

            postDiv.innerHTML = postHtml;

            this.bindRefno(postDiv.querySelector('a.refno'));
            if (file) {
                this.imageExpansion.bindImage(<HTMLElement>postDiv.querySelector('.file'));
            }

            return postDiv;
        }

        getPostNameHtml(name:string) {
            var html = escape(name);
            var i = html.indexOf('!');
            if (i >= 0) {
                html = html.substring(0, i) + '<span class="trip">!' + html.substring(i + 1) + '</span>';
            }
            return html;
        }

        getPostFileSizeText(bytes:number) {
            var prefixes = ['kB', 'MB', 'GB', 'TB'];
            if (bytes == 1) {
                return '1 Byte'
            } else if (bytes < 1000) {
                return bytes + ' Bytes';
            } else {
                for (var i = 0; i < prefixes.length; i++) {
                    var unit = Math.pow(1000, i + 2);
                    if (bytes < unit) {
                        return round((1000 * bytes / unit), 1) + ' ' + prefixes[i];
                    }
                }
            }
        }

        getPostDateText(postDate:number) {
            var date = new Date(postDate);

            // %Y-%m-%d %H:%M:%S
            var output = date.getUTCFullYear() + '-' + lpad(date.getUTCMonth() + 1, 2, '0') + '-' + lpad(date.getUTCDate(), 2, '0') + ' ';
            output += lpad(date.getUTCHours(), 2, '0') + ':' + lpad(date.getUTCMinutes(), 2, '0') + ':' + lpad(date.getUTCSeconds(), 2, '0');
            return output;
        }

        bindPosts(posts:NodeListOf<HTMLElement>) {
            for (var i = 0; i < posts.length; i++) {
                var postElement = posts[i];

                var postObj = {
                    id: 0,
                    refno: 0,
                    date: 0,
                    html: null,
                    name: null,
                    modCode: null,
                    subject: null,
                    file: null
                };

                var checkbox = <HTMLInputElement>postElement.querySelector('input[type="checkbox"]');
                postObj.id = parseInt(checkbox.value);
                postObj.refno = parseInt(postElement.id.substr(1));
                postObj.date = parseInt(postElement.dataset['date']);

                var textElement = postElement.querySelector('.styled-text');
                if (textElement) {
                    var textHtml = textElement.innerHTML.trim();
                    if (textHtml) {
                        postObj.html = textHtml;
                    }
                }

                var nameText = postElement.querySelector('.header .name').textContent.trim();
                if (nameText) {
                    postObj.name = nameText;
                }

                var modCodeElement = postElement.querySelector('.header .modcode');
                if (modCodeElement) {
                    var modCodeText = modCodeElement.textContent;
                    if (modCodeText) {
                        postObj.modCode = modCodeText;
                    }
                }

                var subjectElement = postElement.querySelector('.header .subject');
                if (subjectElement) {
                    var subjectText = subjectElement.textContent.trim();
                    if (subjectText) {
                        postObj.subject = subjectText;
                    }
                }

                var fileAnchorElement = <HTMLElement>postElement.querySelector('.file');
                if (fileAnchorElement) {
                    var imgElement = <HTMLImageElement>fileAnchorElement.querySelector('img');
                    postObj.file = {
                        'location': fileAnchorElement.getAttribute('href'),
                        'thumbnailLocation': imgElement.src,
                        'thumbnailWidth': imgElement.width,
                        'thumbnailHeight': imgElement.height,
                        'width': fileAnchorElement.dataset['filewidth'],
                        'height': fileAnchorElement.dataset['fileheight'],
                        'size': fileAnchorElement.dataset['filesize'],
                        'name': fileAnchorElement.dataset['filename']
                    }
                }

                this.posts.push(postObj);
            }
        }

        bindRefnos() {
            var refnos = document.querySelectorAll('a.refno');
            for (var i = 0; i < refnos.length; i++) {
                var refno = refnos[i];
                this.bindRefno(refno);
            }
        }

        bindRefno(refno) {
            refno.addEventListener('click', function(event) {
                event.preventDefault();
                var refnoText = this.textContent;
                var refnoNumber = parseInt(refnoText.substring(refnoText.indexOf('#') + 1).trim());
                context.qr.show();
                context.qr.addRefno(refnoNumber);
            });
        }
    }
}
