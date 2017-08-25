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
            let list = this.callbacks[name];
            if (!list) {
                list = [];
                this.callbacks[name] = list;
            }
            list.push(func);
        }

        onStorageChanged(event) {
            console.log(event);
        }

        addWatch(watch: Watch) {
            this.data['watches'].push(watch.toObject());
            this.flush();
            this.notify('watches');
        }

        deleteWatch(toDelete: Watch) {
            let watches = this.data['watches'];
            for (let i = 0; i < watches.length; i++) {
                let watch = Watch.fromObject(watches[i]);
                if (watch.equals(toDelete)) {
                    watches.splice(i, 1);
                    break;
                }
            }
            this.flush();
            this.notify('watches');
        }

        getWatches() {
            let res = [];
            let watches = this.data['watches'];
            for (let i = 0; i < watches.length; i++) {
                res.push(Watch.fromObject(watches[i]));
            }
            return res;
        }

        private notify(name: string) {
            if (name in this.callbacks) {
                let list = this.callbacks[name];
                for (let i = 0; i < list.length; i++) {
                    list[i]();
                }
            }
        }

        private flush() {
            this.localStorage.setItem('uchan', JSON.stringify(this.data));
        }
    }
}
