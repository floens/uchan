namespace uchan {
    interface PersistableConstructor {
        new(): Persistable;
    }

    export interface Persistable {
        fromObject(obj: any);

        toObject(): any;
    }

    export class Persistence {
        prefix = 'uchan_';

        localStorage: Storage;

        callbacks: { [key: string]: (() => void) [] } = {};

        constructor() {
            this.localStorage = window.localStorage;
            window.addEventListener("storage", (e) => this.onStorageChanged(e));
        }

        persist(key: string, result: Persistable) {
            let finalKey = this.prefix + key;
            this.localStorage.setItem(finalKey, JSON.stringify(result.toObject()))
        }

        persistList(key: string, result: Persistable[]) {
            let finalKey = this.prefix + key;
            let objects = [];
            for (let i = 0; i < result.length; i++) {
                objects.push(result[i].toObject());
            }
            this.localStorage.setItem(finalKey, JSON.stringify(objects));
        }

        retrieve(key: string, constructor: PersistableConstructor): Persistable {
            let finalKey = this.prefix + key;
            let value = JSON.parse(this.localStorage.getItem(finalKey));
            if (value == null) {
                return null;
            }

            let result = new constructor();
            result.fromObject(value);
            return result;
        }

        retrieveList(key: string, constructor: PersistableConstructor): Persistable[] {
            let finalKey = this.prefix + key;
            let values = JSON.parse(this.localStorage.getItem(finalKey));
            if (values == null) {
                return [];
            }

            let results = [];
            for (let i = 0; i < values.length; i++) {
                let result = new constructor();
                result.fromObject(values[i]);
                results.push(result);
            }

            return results;
        }

        onStorageChanged(event: StorageEvent) {
            if (event.key.indexOf(this.prefix) == 0) {
                let finalKey = event.key.substr(this.prefix.length);

                if (finalKey in this.callbacks) {
                    let callbacks = this.callbacks[finalKey];
                    for (let i = 0; i < callbacks.length; i++) {
                        callbacks[i]();
                    }
                }
            }
        }

        addCallback(name: string, func: () => void) {
            let list = this.callbacks[name];
            if (!list) {
                list = [];
                this.callbacks[name] = list;
            }
            list.push(func);
        }
    }
}
