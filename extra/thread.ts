/// <reference path="extra.ts" />

module uchan {
    export class Post {
        id: number;
        refno: number;
        date: number;
        html: string;
        name: string;
        modCode: string;
        subject: string;
        files: PostFile[] = [];

        references: number[] = [];
        referencedBy: number[] = [];

        observers: ((post: Post) => void)[] = [];

        // This dependency should obviously not exist, but we want to create a map in the PostView to map posts to views,
        // but because there is no way to map objects to objects natively in es5, this is way more efficient than hacking around that.
        views: PostView[] = [];

        resolve() {
            if (this.html) {
                // TODO
                let re = />&gt;&gt;(\d+)</g;
                let res;
                while (res = re.exec(this.html)) {
                    this.references.push(parseInt(res[1]));
                }
            }
        }

        resolveBackrefs(posts: Post[]) {
            let oldReferencedBy = this.referencedBy;

            this.referencedBy = [];
            for (let i = 0; i < posts.length; i++) {
                let post = posts[i];
                if (post.references.indexOf(this.refno) >= 0) {
                    this.referencedBy.push(post.refno);
                }
            }

            if (!arrayEquals(oldReferencedBy, this.referencedBy)) {
                this.notify();
            }
        }

        observe(callback: (post: Post) => void) {
            this.observers.push(callback);
        }

        unobserve(callback: (post: Post) => void) {
            let i = this.observers.indexOf(callback);
            if (i >= 0) {
                this.observers.splice(i, 1);
            }
        }

        isObserving(callback: (post: Post) => void) {
            return this.observers.indexOf(callback) >= 0;
        }

        notify() {
            for (let i = 0; i < this.observers.length; i++) {
                this.observers[i](this);
            }
        }
    }

    export class PostFile {
        location: string;
        thumbnailLocation: string;
        thumbnailWidth: number;
        thumbnailHeight: number;
        width: number;
        height: number;
        size: number;
        name: string;
    }

    export class Thread {
        posts: Post[] = [];

        observers: ((threadView: Thread) => void)[] = [];

        constructor() {
        }

        observe(callback: (threadView: Thread) => void) {
            this.observers.push(callback);
        }

        unobserve(callback: (threadView: Thread) => void) {
            let i = this.observers.indexOf(callback);
            if (i >= 0) {
                this.observers.splice(i, 1);
            }
        }

        notify() {
            for (let i = 0; i < this.observers.length; i++) {
                this.observers[i](this);
            }
        }

        findByRefno(refno: number): Post {
            for (let i = 0; i < this.posts.length; i++) {
                if (this.posts[i].refno == refno) {
                    return this.posts[i];
                }
            }
            return null;
        }

        update(remoteThread) {
            let remotePosts = remoteThread.posts;
            let newPosts = [];
            for (let i = 0; i < remotePosts.length; i++) {
                let remotePost = remotePosts[i];

                let has = false;
                for (let j = 0; j < this.posts.length; j++) {
                    let post = this.posts[j];
                    if (post.id == remotePost.id) {
                        has = true;
                        break;
                    }
                }

                if (!has) {
                    let post = new Post();

                    post.id = remotePost.id;
                    post.refno = remotePost.refno;
                    post.date = remotePost.date;
                    post.html = remotePost.html || null;
                    post.name = remotePost.name || null;
                    post.modCode = remotePost.modCode || null;
                    post.subject = remotePost.subject || null;
                    if (remotePost.files) {
                        for (let i = 0; i < remotePost.files.length; i++) {
                            let remoteFile = remotePost.files[i];
                            let postFile = new PostFile();
                            postFile.location = remoteFile.location;
                            postFile.thumbnailLocation = remoteFile.thumbnailLocation;
                            postFile.thumbnailWidth = remoteFile.thumbnailWidth;
                            postFile.thumbnailHeight = remoteFile.thumbnailHeight;
                            postFile.width = remoteFile.width;
                            postFile.height = remoteFile.height;
                            postFile.size = remoteFile.size;
                            postFile.name = remoteFile.name;
                            post.files.push(postFile);
                        }
                    }
                    post.resolve();

                    newPosts.push(post);
                }
            }

            this.posts.push(...newPosts);

            for (let i = 0; i < this.posts.length; i++) {
                this.posts[i].resolveBackrefs(this.posts);
            }

            this.notify();
        }

        loadFromPostElements(postsElement: HTMLElement) {
            let posts = <NodeListOf<HTMLElement>>postsElement.querySelectorAll('.post');

            for (let i = 0; i < posts.length; i++) {
                let postElement = posts[i];

                let post = new Post();

                let checkbox = <HTMLInputElement>postElement.querySelector('input[type="checkbox"]');
                post.id = parseInt(checkbox.value);
                post.refno = parseInt(postElement.id.substr(1));
                post.date = parseInt(postElement.dataset['date']);

                let textElement = postElement.querySelector('.styled-text');
                if (textElement) {
                    let textHtml = textElement.innerHTML.trim();
                    if (textHtml) {
                        post.html = textHtml;
                    }
                }

                let nameText = postElement.querySelector('.header .name').textContent.trim();
                if (nameText) {
                    post.name = nameText;
                }

                let modCodeElement = postElement.querySelector('.header .modcode');
                if (modCodeElement) {
                    let modCodeText = modCodeElement.textContent;
                    if (modCodeText) {
                        post.modCode = modCodeText;
                    }
                }

                let subjectElement = postElement.querySelector('.header .subject');
                if (subjectElement) {
                    let subjectText = subjectElement.textContent.trim();
                    if (subjectText) {
                        post.subject = subjectText;
                    }
                }

                let files = <NodeListOf<HTMLElement>>postElement.querySelectorAll('.file');

                for (let i = 0; i < files.length; i++) {
                    let fileElement = files[i];
                    let fileAnchorElement = <HTMLAnchorElement>fileElement.querySelector('a.file-link');
                    let imgElement = <HTMLImageElement>fileElement.querySelector('img');

                    let file = new PostFile();

                    file.location = fileAnchorElement.getAttribute('href');
                    file.thumbnailLocation = imgElement.src;
                    file.thumbnailWidth = imgElement.width;
                    file.thumbnailHeight = imgElement.height;
                    file.width = parseInt(fileAnchorElement.dataset['filewidth']);
                    file.height = parseInt(fileAnchorElement.dataset['fileheight']);
                    file.size = parseInt(fileAnchorElement.dataset['filesize']);
                    file.name = fileAnchorElement.dataset['filename'];

                    post.files.push(file);
                }

                post.resolve();

                this.posts.push(post);
            }

            for (let i = 0; i < this.posts.length; i++) {
                this.posts[i].resolveBackrefs(this.posts);
            }
        }
    }
}
