namespace uchan {
    export class ImageExpansion {
        constructor() {
        }

        bindImages() {
            var images = <NodeListOf<HTMLElement>>document.querySelectorAll('.post .file');
            for (var i = 0; i < images.length; i++) {
                var image = images[i];
                this.bindImage(image);
            }
        }

        bindImage(container:HTMLElement) {
            var link = <HTMLAnchorElement>container.querySelector('a');
            var image = <HTMLImageElement>container.querySelector('img');
            image.addEventListener('click', (event) => {
                if (event.button == 0) {
                    event.preventDefault();

                    var expanded = link.dataset['expanded'] == 'true';
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

            var width = parseInt(link.dataset['filewidth']);
            var height = parseInt(link.dataset['fileheight']);

            var bb = container.getBoundingClientRect();
            var availableWidth = document.documentElement.clientWidth;
            var availableHeight = document.documentElement.clientHeight;

            if (width > availableWidth || height > availableHeight) {
                var ratio = Math.min(availableWidth / width, availableHeight / height);
                width *= ratio;
                height *= ratio;
            }

            var leftMargin = 0;
            if (width > availableWidth - bb.left) {
                leftMargin = -bb.left;
            }

            link.dataset['expanded'] = 'true';
            image.src = link.href;
            image.style.marginLeft = (leftMargin) + 'px';
            image.width = width;
            image.height = height;
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
