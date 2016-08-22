namespace uchan {
    export class Persistence {
        localStorage: Storage;

        data: any;

        callbacks: {[key: string]: (() => void) []} = {};

        constructor() {
            this.localStorage = window.localStorage;

            if (this.localStorage.getItem('uchan') == null) {
                this.localStorage.setItem('uchan', '{}');
            }
            this.data = JSON.parse(this.localStorage.getItem('uchan'));

            if (!('watches' in this.data)) {
                this.data['watches'] = [];
            }
            this.flush();

            window.addEventListener("storage", (e) => this.onStorageChanged(e));
        }

        addCallback(name: string, func: () => void) {
            var list = this.callbacks[name];
            if (!list) {
                list = [];
                this.callbacks[name] = list;
            }
            list.push(func);
        }

        onStorageChanged(event) {
            console.log(event);
        }

        addWatch(board, thread) {
            this.data['watches'].push({
                'board': board,
                'thread': thread
            });
            this.flush();
            this.notify('watches');
        }

        deleteWatch(item) {
            var watches = this.data['watches'];
            for (var i = 0; i < watches.length; i++) {
                var watch = watches[i];
                if (watch['board'] == item['board'] && watch['thread'] == item['thread']) {
                    watches.splice(i, 1);
                    break;
                }
            }
            this.flush();
            this.notify('watches');
        }

        getWatches() {
            return this.data['watches'];
        }

        private notify(name: string) {
            if (name in this.callbacks) {
                var list = this.callbacks[name];
                for (var i = 0; i < list.length; i++) {
                    list[i]();
                }
            }
        }

        private flush() {
            this.localStorage.setItem('uchan', JSON.stringify(this.data));
        }
    }
}
