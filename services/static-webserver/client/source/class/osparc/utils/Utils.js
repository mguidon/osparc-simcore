/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/**
 * @ignore(URL)
 * @ignore(sessionStorage)
 * @ignore(fetch)
 * @ignore(URLSearchParams)
 */

/**
 * Sandbox of static methods that do not fit in other utils classes.
 */

qx.Class.define("osparc.utils.Utils", {
  type: "static",

  statics: {
    localCache: {
      setLocalStorageItem: function(key, value) {
        window.localStorage.setItem(key, value);
      },
      getLocalStorageItem: function(name) {
        return window.localStorage.getItem(name);
      },

      setTheme: function(themeName) {
        this.setLocalStorageItem("themeName", themeName);
      },
      getTheme: function() {
        return this.getLocalStorageItem("themeName");
      },

      serviceToFavs: function(serviceKey) {
        let serviceFavs = this.getLocalStorageItem("services");
        if (serviceFavs) {
          serviceFavs = JSON.parse(serviceFavs);
        } else {
          serviceFavs = {};
        }
        if (serviceFavs && (serviceKey in serviceFavs)) {
          serviceFavs[serviceKey]["hits"]++;
        } else {
          serviceFavs[serviceKey] = {
            hits: 1
          };
        }
        this.setLocalStorageItem("services", JSON.stringify(serviceFavs));
      },

      getFavServices: function() {
        const serviceFavs = this.getLocalStorageItem("services");
        if (serviceFavs) {
          return JSON.parse(serviceFavs);
        }
        return [];
      },

      getSortedFavServices: function() {
        const serviceFavs = this.getFavServices();
        const favServices = Object.keys().sort((a, b) => serviceFavs[b]["hits"] - serviceFavs[a]["hits"]);
        return favServices;
      }
    },

    getUniqueStudyName: function(preferredName, list) {
      let title = preferredName;
      const existingTitles = list.map(study => study.name);
      if (existingTitles.includes(title)) {
        let cont = 1;
        while (existingTitles.includes(`${title} (${cont})`)) {
          cont++;
        }
        title += ` (${cont})`;
      }
      return title;
    },

    checkIsOnScreen: function(elem) {
      const isInViewport = element => {
        if (element) {
          const rect = element.getBoundingClientRect();
          const html = document.documentElement;
          return (
            rect.width > 0 &&
            rect.height > 0 &&
            rect.top >= 0 &&
            rect.left >= 0 &&
            // a bit of tolerance to deal with zooming factors
            rect.bottom*0.95 <= (window.innerHeight || html.clientHeight) &&
            rect.right*0.95 <= (window.innerWidth || html.clientWidth)
          );
        }
        return false;
      };

      const domElem = elem.getContentElement().getDomElement();
      const checkIsOnScreen = isInViewport(domElem);
      return checkIsOnScreen;
    },

    toTwoDecimals: function(value) {
      return Math.round(100*value)/100;
    },

    computeServiceUrl: function(resp) {
      const data = {
        srvUrl: null,
        isDynamicV2: null
      };
      const isDynamicV2 = resp["boot_type"] === "V2" || false;
      data["isDynamicV2"] = isDynamicV2;
      if (isDynamicV2) {
        // dynamic service
        const srvUrl = window.location.protocol + "//" + resp["service_uuid"] + ".services." + window.location.host;
        data["srvUrl"] = srvUrl;
      } else {
        // old implementation
        const servicePath = resp["service_basepath"];
        const entryPointD = resp["entry_point"];
        if (servicePath) {
          const entryPoint = entryPointD ? ("/" + entryPointD) : "/";
          const srvUrl = servicePath + entryPoint;
          data["srvUrl"] = srvUrl;
        }
      }
      return data;
    },

    computeServiceRetrieveUrl: function(srvUrl) {
      const urlRetrieve = srvUrl + "/retrieve";
      return urlRetrieve.replace("//retrieve", "/retrieve");
    },

    computeServiceV2RetrieveUrl: function(studyId, nodeId) {
      const urlBase = window.location.protocol + "//" + window.location.host + "/v0";
      return urlBase + "/projects/" + studyId + "/nodes/" + nodeId + ":retrieve";
    },

    setZoom: function(el, zoom) {
      const transformOrigin = [0, 0];
      const p = ["webkit", "moz", "ms", "o"];
      const s = `scale(${zoom})`;
      const oString = (transformOrigin[0] * 100) + "% " + (transformOrigin[1] * 100) + "%";
      for (let i = 0; i < p.length; i++) {
        el.style[p[i] + "Transform"] = s;
        el.style[p[i] + "TransformOrigin"] = oString;
      }
      el.style["transform"] = s;
      el.style["transformOrigin"] = oString;
    },

    isMouseOnElement: function(element, event, offset = 0) {
      const domElement = element.getContentElement().getDomElement();
      const boundRect = domElement.getBoundingClientRect();
      if (event.x > boundRect.x - offset &&
        event.y > boundRect.y - offset &&
        event.x < (boundRect.x + boundRect.width) + offset &&
        event.y < (boundRect.y + boundRect.height) + offset) {
        return true;
      }
      return false;
    },

    sleep: function(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    isValidHttpUrl: function(string) {
      let url;
      try {
        url = new URL(string);
      } catch (_) {
        return false;
      }
      return url.protocol === "http:" || url.protocol === "https:";
    },

    isDevelopmentPlatform: function() {
      return new Promise(resolve => {
        osparc.utils.LibVersions.getPlatformName()
          .then(platformName => resolve(["dev", "master"].includes(platformName)));
      });
    },

    getProductName: function() {
      return qx.core.Environment.get("product.name");
    },

    isProduct: function(productName) {
      const product = qx.core.Environment.get("product.name");
      return (productName === product);
    },

    getEditButton: function() {
      const button = new qx.ui.form.Button(null, "@FontAwesome5Solid/pencil-alt/12").set({
        allowGrowY: false,
        padding: 3,
        maxWidth: 20
      });
      return button;
    },

    getViewButton: function() {
      const button = new qx.ui.form.Button(null, "@FontAwesome5Solid/eye/12").set({
        allowGrowY: false,
        padding: 3,
        maxWidth: 20
      });
      return button;
    },

    getCopyButton: function() {
      const button = new qx.ui.form.Button(null, "@FontAwesome5Solid/copy/12").set({
        allowGrowY: false,
        padding: 3,
        maxWidth: 20
      });
      return button;
    },

    /**
      * @param value {Date Object} Date Object
      */
    formatDate: function(value) {
      // create a date format like "Oct. 19, 2018 11:31 AM"
      const dateFormat = new qx.util.format.DateFormat(
        qx.locale.Date.getDateFormat("medium")
      );

      let dateStr = null;
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      if (today.toDateString() === value.toDateString()) {
        dateStr = qx.locale.Manager.tr("Today");
      } else if (yesterday.toDateString() === value.toDateString()) {
        dateStr = qx.locale.Manager.tr("Yesterday");
      } else {
        dateStr = dateFormat.format(value);
      }
      return dateStr;
    },

    /**
      * @param value {Date Object} Date Object
      */
    formatTime: function(value, long = false) {
      const timeFormat = new qx.util.format.DateFormat(
        qx.locale.Date.getTimeFormat(long ? "long" : "short")
      );
      const timeStr = timeFormat.format(value);
      return timeStr;
    },

    /**
      * @param value {Date Object} Date Object
      */
    formatDateAndTime: function(value) {
      return osparc.utils.Utils.formatDate(value) + " " + osparc.utils.Utils.formatTime(value);
    },

    daysBetween: function(date1, date2) {
      // The number of milliseconds in one day
      const ONE_DAY = 1000 * 60 * 60 * 24;
      // Calculate the difference in milliseconds
      const differenceMs = date2 - date1;
      // Convert back to days and return
      return Math.round(differenceMs / ONE_DAY);
    },

    getNameFromEmail: function(email) {
      return email.split("@")[0];
    },

    uuidv4: function() {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ window.crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    },

    isInZ43: function() {
      return window.location.hostname.includes("speag");
    },

    getLogoPath: function() {
      let logosPath = null;
      const colorManager = qx.theme.manager.Color.getInstance();
      const textColor = colorManager.resolve("text");
      const lightLogo = this.getColorLuminance(textColor) > 0.4;
      const product = qx.core.Environment.get("product.name");
      switch (product) {
        case "s4l":
          logosPath = lightLogo ? "osparc/s4l_zmt-white.svg" : "osparc/s4l_zmt-black.svg";
          break;
        case "tis": {
          logosPath = lightLogo ? "osparc/tip_itis-white.svg" : "osparc/tip_itis-black.svg";
          break;
        }
        default: {
          logosPath = lightLogo ? "osparc/osparc-white.svg" : "osparc/osparc-black.svg";
          break;
        }
      }
      return logosPath;
    },

    addBorder: function(widget, width = 1, color = "transparent") {
      widget.getContentElement().setStyle("border", width+"px solid " + color);
    },

    removeBorder: function(widget) {
      widget.getContentElement().setStyle("border", "0px solid");
    },

    hideBorder: function(widget) {
      widget.getContentElement().setStyle("border", "1px solid transparent");
    },

    __setStyleToIFrame: function(domEl) {
      if (domEl && domEl.contentDocument && domEl.contentDocument.documentElement) {
        const iframeDocument = domEl.contentDocument.documentElement;
        const colorManager = qx.theme.manager.Color.getInstance();
        const bgColor = colorManager.resolve("loading-page-background-color");
        const textColor = colorManager.resolve("loading-page-text");
        const spinnerColor = colorManager.resolve("loading-page-spinner");
        iframeDocument.style.setProperty("--background-color", bgColor);
        iframeDocument.style.setProperty("--text-color", textColor);
        iframeDocument.style.setProperty("--spinner-color", spinnerColor);
      }
    },

    compareVersionNumbers: function(v1, v2) {
      // https://stackoverflow.com/questions/6832596/how-to-compare-software-version-number-using-js-only-number/47500834
      // - a number < 0 if a < b
      // - a number > 0 if a > b
      // - 0 if a = b
      const regExStrip0 = /(\.0+)+$/;
      const segmentsA = v1.replace(regExStrip0, "").split(".");
      const segmentsB = v2.replace(regExStrip0, "").split(".");
      const l = Math.min(segmentsA.length, segmentsB.length);

      for (let i = 0; i < l; i++) {
        const diff = parseInt(segmentsA[i], 10) - parseInt(segmentsB[i], 10);
        if (diff) {
          return diff;
        }
      }
      return segmentsA.length - segmentsB.length;
    },

    // deep clone of nested objects
    deepCloneObject: function(src) {
      return JSON.parse(JSON.stringify(src));
    },

    prettifyJson: function(json) {
      return JSON.stringify(json, undefined, 2);
    },

    getRandomColor: function() {
      let letters = "0123456789ABCDEF";
      let color = "#";
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    },

    getColorLuminance: function(color) {
      const rgb = qx.util.ColorUtil.isRgbString(color) || qx.util.ColorUtil.isRgbaString(color) ? qx.util.ColorUtil.stringToRgb(color) : qx.util.ColorUtil.hexStringToRgb(color);
      const luminance = 0.2126*(rgb[0]/255) + 0.7152*(rgb[1]/255) + 0.0722*(rgb[2]/255);
      return luminance;
    },

    getContrastedTextColor: function(color) {
      const L = this.getColorLuminance(color);
      return L > 0.35 ? "contrasted-text-dark" : "contrasted-text-light";
    },

    getRoundedBinaryColor: function(color) {
      const L = this.getColorLuminance(color);
      return L > 0.35 ? "#FFF" : "#000";
    },

    bytesToSize: function(bytes) {
      const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
      if (bytes == 0) {
        return "0 Bytes";
      }
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + " " + sizes[i];
    },

    bytesToGB: function(bytes) {
      const b2gb = 1024*1024*1024;
      return Math.round(100*bytes/b2gb)/100;
    },

    retrieveURLAndDownload: function(locationId, fileId) {
      let fileName = fileId.split("/");
      fileName = fileName[fileName.length-1];
      const download = true;
      const dataStore = osparc.store.Data.getInstance();
      dataStore.getPresignedLink(download, locationId, fileId)
        .then(presignedLinkData => {
          if (presignedLinkData.resp) {
            const link = presignedLinkData.resp.link;
            const fileNameFromLink = this.fileNameFromPresignedLink(link);
            fileName = fileNameFromLink ? fileNameFromLink : fileName;
            this.downloadLink(link, "GET", fileName);
          }
        });
    },

    downloadLink: function(url, method, fileName, downloadStartedCB) {
      return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        xhr.responseType = "blob";
        xhr.addEventListener("readystatechange", () => {
        // xhr.onreadystatechange = () => {
          if (xhr.readyState === XMLHttpRequest.HEADERS_RECEIVED) {
            // The responseType value can be changed at any time before the readyState reaches 3.
            // When the readyState reaches 2, we have access to the response headers to make that decision with.
            if (xhr.status >= 200 && xhr.status < 400) {
              xhr.responseType = "blob";
            } else {
              // get ready for handling an error
              xhr.responseType = "text";
            }
          }
        });
        xhr.addEventListener("progress", () => {
          if (xhr.readyState === XMLHttpRequest.LOADING) {
            if (xhr.status === 0 || (xhr.status >= 200 && xhr.status < 400)) {
              if (downloadStartedCB) {
                downloadStartedCB();
              }
            }
          }
        });
        xhr.addEventListener("load", () => {
          if (xhr.status == 200) {
            let blob = new Blob([xhr.response]);
            let urlBlob = window.URL.createObjectURL(blob);
            if (!fileName) {
              fileName = this.self().filenameFromContentDisposition(xhr);
            }
            this.self().downloadContent(urlBlob, fileName);
            resolve();
          } else {
            reject(xhr);
          }
        });
        xhr.addEventListener("error", () => reject(xhr));
        xhr.addEventListener("abort", () => reject(xhr));
        xhr.send();
      });
    },

    downloadContent: function(content, filename = "file") {
      let downloadAnchorNode = document.createElement("a");
      downloadAnchorNode.setAttribute("href", content);
      downloadAnchorNode.setAttribute("download", filename);
      downloadAnchorNode.click();
      downloadAnchorNode.remove();
    },

    filenameFromContentDisposition: function(xhr) {
      // https://stackoverflow.com/questions/40939380/how-to-get-file-name-from-content-disposition
      let filename = "";
      const disposition = xhr.getResponseHeader("Content-Disposition");
      if (disposition && disposition.indexOf("attachment") !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, "");
        }
      }
      return filename;
    },

    fileNameFromPresignedLink: function(link) {
      // regex match /([^/]+)\?
      const fileNames = new URL(link).pathname.split("/");
      if (fileNames.length) {
        return fileNames.pop();
      }
      return null;
    },

    /**
     * Function that takes an indefinite number of strings as separated parameters, and concatenates them capitalizing the first letter.
     */
    capitalize: function() {
      let res = "";
      for (let i=0; i<arguments.length; i++) {
        if (typeof arguments[i] !== "string" && arguments[i] instanceof String === false) {
          continue;
        }
        const capitalized = arguments[i].charAt(0).toUpperCase() + arguments[i].slice(1);
        res = res.concat(capitalized);
      }
      return res;
    },

    /**
     * Copies the given text to the clipboard
     *
     * @param text {String} Text to be copied
     * @return {Boolean} True if it was successful
     */
    copyTextToClipboard: function(text) {
      // from https://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript
      const textArea = document.createElement("textarea");

      //
      // *** This styling is an extra step which is likely not required. ***
      //
      // Why is it here? To ensure:
      // 1. the element is able to have focus and selection.
      // 2. if element was to flash render it has minimal visual impact.
      // 3. less flakyness with selection and copying which **might** occur if
      //    the textarea element is not visible.
      //
      // The likelihood is the element won't even render, not even a
      // flash, so some of these are just precautions. However in
      // Internet Explorer the element is visible whilst the popup
      // box asking the user for permission for the web page to
      // copy to the clipboard.
      //

      // Place in top-left corner of screen regardless of scroll position.
      // Ensure it has a small width and height. Setting to 1px / 1em
      // doesn't work as this gives a negative w/h on some browsers.
      // We don't need padding, reducing the size if it does flash render.
      // Clean up any borders.
      // Avoid flash of white box if rendered for any reason.
      textArea.style = {
        position: "fixed",
        top: 0,
        left: 0,
        width: "2em",
        height: "2em",
        padding: 0,
        border: "none",
        outline: "none",
        boxShadow: "none",
        background: "transparent"
      };
      textArea.value = text;

      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch (err) {
        console.error("Oops, unable to copy");
      }

      document.body.removeChild(textArea);

      if (copied) {
        osparc.component.message.FlashMessenger.getInstance().logAs(qx.locale.Manager.tr("Copied to clipboard"));
      }

      return copied;
    },

    cookie: {
      setCookie: (cname, cvalue, exdays) => {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires="+d.toUTCString();
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
      },

      getCookie: cname => {
        const name = cname + "=";
        const ca = document.cookie.split(";");
        for (let i = 0; i < ca.length; i++) {
          let c = ca[i];
          while (c.charAt(0) == " ") {
            c = c.substring(1);
          }
          if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
          }
        }
        return null;
      },

      deleteCookie: cname => {
        document.cookie = cname + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      }
    },

    parseURLFragment: () => {
      let urlHash = window.location.hash.slice(1);
      const parsedFragment = {};
      if (urlHash.length) {
        urlHash = urlHash.split("?");
        if (urlHash.length < 3) {
          // Nav
          urlHash[0].split("/").forEach(fragmentPart => {
            if (fragmentPart.length) {
              parsedFragment.nav = parsedFragment.nav || [];
              parsedFragment.nav.push(decodeURIComponent(fragmentPart));
            }
          });
          if (urlHash.length === 2) {
            // Params
            parsedFragment.params = parsedFragment.params || {};
            urlHash[1].replace(/([^=&]+)=([^&]*)/g, function(m, key, value) {
              parsedFragment.params[decodeURIComponent(key)] = decodeURIComponent(value);
            });
          }
        } else {
          console.error("URL fragment doesn't have the correct format.");
          return null;
        }
      }
      return parsedFragment;
    },

    getParamFromURL: (url, param) => {
      const urlParams = new URLSearchParams(url);
      return urlParams.get(param);
    },

    hasParamFromURL: (url, param) => {
      const urlParams = new URLSearchParams(url);
      return urlParams.has(param);
    },

    isUrl: url => /^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/gm.test(url),

    setIdToWidget: (qWidget, id) => {
      if (qWidget.getContentElement) {
        qWidget.getContentElement().setAttribute("osparc-test-id", id);
      }
    },

    setMoreToWidget: (qWidget, id) => {
      if (qWidget.getContentElement) {
        qWidget.getContentElement().setAttribute("osparc-test-more", id);
      }
    },

    getClientSessionID: function() {
      // https://stackoverflow.com/questions/11896160/any-way-to-identify-browser-tab-in-javascript
      const clientSessionID = sessionStorage.getItem("clientsessionid") ? sessionStorage.getItem("clientsessionid") : osparc.utils.Utils.uuidv4();
      sessionStorage.setItem("clientsessionid", clientSessionID);
      return clientSessionID;
    },

    getFreeDistanceToWindowEdges: function(layoutItem) {
      const domElement = layoutItem.getContentElement().getDomElement();
      if (domElement === null) {
        return null;
      }
      const location = qx.bom.element.Location.get(domElement);
      return {
        top: location.top,
        right: window.innerWidth - location.right,
        bottom: window.innerHeight - location.bottom,
        left: location.left
      };
    },

    fetchJSON: function() {
      return fetch.apply(null, arguments).then(response => response.json());
    },

    firstsUp: function(...args) {
      const labels = [];
      args.forEach(arg => labels.push(qx.lang.String.firstUp(arg)));
      return labels.join(" ");
    },

    isObject: function(v) {
      return typeof v === "object" && v !== null;
    },

    addClass: function(element, className) {
      if (element) {
        const currentClass = element.getAttribute("class");
        if (currentClass && currentClass.includes(className.trim())) {
          return;
        }
        element.setAttribute("class", ((currentClass || "") + " " + className).trim());
      }
    },

    removeClass: function(element, className) {
      const currentClass = element.getAttribute("class");
      if (currentClass) {
        const regex = new RegExp(className.trim(), "g");
        element.setAttribute("class", currentClass.replace(regex, ""));
      }
    },

    closeHangingWindows: function() {
      // close windows
      const children = qx.core.Init.getApplication().getRoot().getChildren();
      children.forEach(child => {
        if (child.classname === "osparc.ui.window.Window") {
          child.close();
        }
      });
    }
  }
});