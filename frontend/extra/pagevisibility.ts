interface VisibilityCallback {
  (visible: boolean): void;
}

export class PageVisibility {
  private static eventListenerRegistered = false;
  private static listeners: VisibilityCallback[] = [];

  static isVisible(): boolean {
    return !document.hidden;
  }

  static addListener(listener: VisibilityCallback) {
    if (!this.eventListenerRegistered) {
      this.eventListenerRegistered = true;
      document.addEventListener('visibilitychange', (e) => {
        let visible = this.isVisible();
        for (let i = 0; i < this.listeners.length; i++) {
          this.listeners[i](visible);
        }
      });
    }

    this.listeners.push(listener);
  }

  static removeListener(listener: VisibilityCallback) {
    let index = this.listeners.indexOf(listener);
    if (index >= 0) {
      PageVisibility.listeners.splice(index, 1);
    }
  }
}
