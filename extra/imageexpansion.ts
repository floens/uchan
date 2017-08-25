namespace uchan {
    export class ImageExpansion {
        constructor() {
        }

        bindImages() {
            let images = <NodeListOf<HTMLElement>>document.querySelectorAll('.post .file');
            for (let i = 0; i < images.length; i++) {
                let image = images[i];
                this.bindImage(image);
            }
        }

        bindImage(container:HTMLElement) {
            let link = <HTMLAnchorElement>container.querySelector('a');
            let image = <HTMLImageElement>container.querySelector('img');
            image.addEventListener('click', (event) => {
                if (event.button == 0 && !event.shiftKey && !event.ctrlKey && !event.metaKey) {
                    event.preventDefault();

                    let expanded = link.dataset['expanded'] == 'true';
                    if (expanded) {
                        this.close(container, link, image);
                    } else {
                        this.expand(container, link, image);
                    }
                }
            });
        }

        expand(container:HTMLElement, link:HTMLAnchorElement, image:HTMLImageElement) {
            if (!link.dataset['thumbnail']) {
                link.dataset['thumbnail'] = image.src;
                link.dataset['thumbnailwidth'] = image.width.toString();
                link.dataset['thumbnailheight'] = image.height.toString();
            }

            let width = parseInt(link.dataset['filewidth']);
            let height = parseInt(link.dataset['fileheight']);

            let availableWidth = document.documentElement.clientWidth;
            let availableHeight = document.documentElement.clientHeight;

            if (width > availableWidth || height > availableHeight) {
                let ratio = Math.min(availableWidth / width, availableHeight / height);
                width *= ratio;
                height *= ratio;
            }

            link.dataset['expanded'] = 'true';
            image.src = link.href;
            image.width = width;
            image.height = height;

            let bb = image.getBoundingClientRect();
            let leftMargin = 0;
            if (width > availableWidth - bb.left) {
                leftMargin = -bb.left;
            }
            image.style.marginLeft = (leftMargin) + 'px';
        }

        close(container:HTMLElement, link:HTMLAnchorElement, image:HTMLImageElement) {
            image.src = link.dataset['thumbnail'];
            image.width = parseInt(link.dataset['thumbnailwidth']);
            image.height = parseInt(link.dataset['thumbnailheight']);
            image.style.marginLeft = '0';
            link.dataset['expanded'] = 'false';
        }
    }
}
