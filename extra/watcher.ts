/// <reference path="imageexpansion.ts" />

namespace uchan {
    export class Watcher {
        threadId:number;
        postsElement:HTMLElement;
        statusElement:HTMLElement;
        imageExpansion:ImageExpansion;

        xhr:XMLHttpRequest;
        posts:any[];

        constructor(threadId, postsElement, statusElement, imageExpansion) {
            this.threadId = threadId;
            this.postsElement = postsElement;
            this.statusElement = statusElement;
            this.imageExpansion = imageExpansion;

            this.xhr = null;

            this.posts = [];
        };

        addUpdateListener = function(element:Element) {
            element.addEventListener('click', this.onUpdateElementClickEvent.bind(this));
        };

        setStatus = function(status:string) {
            this.statusElement.textContent = status;
        };

        onUpdateElementClickEvent = function(event:Event) {
            event.preventDefault();
            this.update();
        };

        update = function() {
            if (this.xhr == null) {
                this.setStatus('Updating...');
                this.xhr = xhrJsonGet('/api/thread/' + this.threadId, this.xhrDone.bind(this));
            }
        };

        xhrDone = function(error:Error, data:any) {
            if (error) {
                console.error('watcher error');
            } else {
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
            }

            this.setStatus('');
            this.xhr = null;
        };

        buildPostElement = function(postData:any) {
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
                this.imageExpansion.bindImage(postDiv.querySelector('.file'));
            }

            return postDiv;
        };

        getPostNameHtml = function(name:string) {
            var html = escape(name);
            var i = html.indexOf('!');
            if (i >= 0) {
                html = html.substring(0, i) + '<span class="trip">!' + html.substring(i + 1) + '</span>';
            }
            return html;
        };

        getPostFileSizeText = function(bytes:number) {
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
        };

        getPostDateText = function(postDate:number) {
            var date = new Date(postDate);

            // %Y-%m-%d %H:%M:%S
            var output = date.getUTCFullYear() + '-' + lpad(date.getUTCMonth() + 1, 2, '0') + '-' + lpad(date.getUTCDate(), 2, '0') + ' ';
            output += lpad(date.getUTCHours(), 2, '0') + ':' + lpad(date.getUTCMinutes(), 2, '0') + ':' + lpad(date.getUTCSeconds(), 2, '0');
            return output;
        };

        bindPosts = function(posts:any[]) {
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

                postObj.id = parseInt(postElement.querySelector('input[type="checkbox"]').value);
                postObj.refno = parseInt(postElement.id.substr(1));
                postObj.date = parseInt(postElement.dataset.date);

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

                var fileAnchorElement = postElement.querySelector('.file');
                if (fileAnchorElement) {
                    var imgElement = fileAnchorElement.querySelector('img');
                    postObj.file = {
                        'location': fileAnchorElement.getAttribute('href'),
                        'thumbnailLocation': imgElement.src,
                        'thumbnailWidth': imgElement.width,
                        'thumbnailHeight': imgElement.height,
                        'width': fileAnchorElement.dataset.filewidth,
                        'height': fileAnchorElement.dataset.fileheight,
                        'size': fileAnchorElement.dataset.filesize,
                        'name': fileAnchorElement.dataset.filename
                    }
                }

                this.posts.push(postObj);
            }
        };

        bindRefnos = function() {
            var refnos = document.querySelectorAll('a.refno');
            for (var i = 0; i < refnos.length; i++) {
                var refno = refnos[i];
                this.bindRefno(refno);
            }
        };

        bindRefno = function(refno) {
            refno.addEventListener('click', function(event) {
                event.preventDefault();
                var refnoText = this.textContent;
                var refnoNumber = parseInt(refnoText.substring(refnoText.indexOf('#') + 1).trim());
                context.qr.show();
                context.qr.addRefno(refnoNumber);
            });
        };
    }
}
