(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // ns-hugo:/Users/alex/Desktop/playground/ai-safety-papers/ai-safety-site/themes/hugo-theme-monochrome/assets/lib/js/zooming-v2.1.1.min.js
  var require_zooming_v2_1_1_min = __commonJS({
    "ns-hugo:/Users/alex/Desktop/playground/ai-safety-papers/ai-safety-site/themes/hugo-theme-monochrome/assets/lib/js/zooming-v2.1.1.min.js"(exports, module) {
      !function(t, e) {
        "object" == typeof exports && "undefined" != typeof module ? module.exports = e() : "function" == typeof define && define.amd ? define(e) : (t = t || self).Zooming = e();
      }(exports, function() {
        "use strict";
        var t = "auto", e = "zoom-in", i = "zoom-out", n = "grab", s = "move";
        function o(t2, e2, i2) {
          var n2 = { passive: false };
          !(arguments.length > 3 && void 0 !== arguments[3]) || arguments[3] ? t2.addEventListener(e2, i2, n2) : t2.removeEventListener(e2, i2, n2);
        }
        function r(t2, e2) {
          if (t2) {
            var i2 = new Image();
            i2.onload = function() {
              e2 && e2(i2);
            }, i2.src = t2;
          }
        }
        function a(t2) {
          return t2.dataset.original ? t2.dataset.original : "A" === t2.parentNode.tagName ? t2.parentNode.getAttribute("href") : null;
        }
        function l(t2, e2, i2) {
          !function(t3) {
            var e3 = h.transitionProp, i3 = h.transformProp;
            if (t3.transition) {
              var n3 = t3.transition;
              delete t3.transition, t3[e3] = n3;
            }
            if (t3.transform) {
              var s3 = t3.transform;
              delete t3.transform, t3[i3] = s3;
            }
          }(e2);
          var n2 = t2.style, s2 = {};
          for (var o2 in e2) i2 && (s2[o2] = n2[o2] || ""), n2[o2] = e2[o2];
          return s2;
        }
        var h = { transitionProp: "transition", transEndEvent: "transitionend", transformProp: "transform", transformCssProp: "transform" }, c = h.transformCssProp, u = h.transEndEvent;
        var d = function() {
        }, f = { enableGrab: true, preloadImage: false, closeOnWindowResize: true, transitionDuration: 0.4, transitionTimingFunction: "cubic-bezier(0.4, 0, 0, 1)", bgColor: "rgb(255, 255, 255)", bgOpacity: 1, scaleBase: 1, scaleExtra: 0.5, scrollThreshold: 40, zIndex: 998, customSize: null, onOpen: d, onClose: d, onGrab: d, onMove: d, onRelease: d, onBeforeOpen: d, onBeforeClose: d, onBeforeGrab: d, onBeforeRelease: d, onImageLoading: d, onImageLoaded: d }, p = { init: function(t2) {
          var e2, i2;
          e2 = this, i2 = t2, Object.getOwnPropertyNames(Object.getPrototypeOf(e2)).forEach(function(t3) {
            e2[t3] = e2[t3].bind(i2);
          });
        }, click: function(t2) {
          if (t2.preventDefault(), m(t2)) return window.open(this.target.srcOriginal || t2.currentTarget.src, "_blank");
          this.shown ? this.released ? this.close() : this.release() : this.open(t2.currentTarget);
        }, scroll: function() {
          var t2 = document.documentElement || document.body.parentNode || document.body, e2 = window.pageXOffset || t2.scrollLeft, i2 = window.pageYOffset || t2.scrollTop;
          null === this.lastScrollPosition && (this.lastScrollPosition = { x: e2, y: i2 });
          var n2 = this.lastScrollPosition.x - e2, s2 = this.lastScrollPosition.y - i2, o2 = this.options.scrollThreshold;
          (Math.abs(s2) >= o2 || Math.abs(n2) >= o2) && (this.lastScrollPosition = null, this.close());
        }, keydown: function(t2) {
          (function(t3) {
            return "Escape" === (t3.key || t3.code) || 27 === t3.keyCode;
          })(t2) && (this.released ? this.close() : this.release(this.close));
        }, mousedown: function(t2) {
          if (y(t2) && !m(t2)) {
            t2.preventDefault();
            var e2 = t2.clientX, i2 = t2.clientY;
            this.pressTimer = setTimeout(function() {
              this.grab(e2, i2);
            }.bind(this), 200);
          }
        }, mousemove: function(t2) {
          this.released || this.move(t2.clientX, t2.clientY);
        }, mouseup: function(t2) {
          y(t2) && !m(t2) && (clearTimeout(this.pressTimer), this.released ? this.close() : this.release());
        }, touchstart: function(t2) {
          t2.preventDefault();
          var e2 = t2.touches[0], i2 = e2.clientX, n2 = e2.clientY;
          this.pressTimer = setTimeout(function() {
            this.grab(i2, n2);
          }.bind(this), 200);
        }, touchmove: function(t2) {
          if (!this.released) {
            var e2 = t2.touches[0], i2 = e2.clientX, n2 = e2.clientY;
            this.move(i2, n2);
          }
        }, touchend: function(t2) {
          (function(t3) {
            t3.targetTouches.length;
          })(t2) || (clearTimeout(this.pressTimer), this.released ? this.close() : this.release());
        }, clickOverlay: function() {
          this.close();
        }, resizeWindow: function() {
          this.close();
        } };
        function y(t2) {
          return 0 === t2.button;
        }
        function m(t2) {
          return t2.metaKey || t2.ctrlKey;
        }
        var g = { init: function(t2) {
          this.el = document.createElement("div"), this.instance = t2, this.parent = document.body, l(this.el, { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, opacity: 0 }), this.updateStyle(t2.options), o(this.el, "click", t2.handler.clickOverlay.bind(t2));
        }, updateStyle: function(t2) {
          l(this.el, { zIndex: t2.zIndex, backgroundColor: t2.bgColor, transition: "opacity\n        " + t2.transitionDuration + "s\n        " + t2.transitionTimingFunction });
        }, insert: function() {
          this.parent.appendChild(this.el);
        }, remove: function() {
          this.parent.removeChild(this.el);
        }, fadeIn: function() {
          this.el.offsetWidth, this.el.style.opacity = this.instance.options.bgOpacity;
        }, fadeOut: function() {
          this.el.style.opacity = 0;
        } }, v = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(t2) {
          return typeof t2;
        } : function(t2) {
          return t2 && "function" == typeof Symbol && t2.constructor === Symbol && t2 !== Symbol.prototype ? "symbol" : typeof t2;
        }, b = function(t2, e2) {
          if (!(t2 instanceof e2)) throw new TypeError("Cannot call a class as a function");
        }, w = /* @__PURE__ */ function() {
          function t2(t3, e2) {
            for (var i2 = 0; i2 < e2.length; i2++) {
              var n2 = e2[i2];
              n2.enumerable = n2.enumerable || false, n2.configurable = true, "value" in n2 && (n2.writable = true), Object.defineProperty(t3, n2.key, n2);
            }
          }
          return function(e2, i2, n2) {
            return i2 && t2(e2.prototype, i2), n2 && t2(e2, n2), e2;
          };
        }(), x = Object.assign || function(t2) {
          for (var e2 = 1; e2 < arguments.length; e2++) {
            var i2 = arguments[e2];
            for (var n2 in i2) Object.prototype.hasOwnProperty.call(i2, n2) && (t2[n2] = i2[n2]);
          }
          return t2;
        }, O = { init: function(t2, e2) {
          this.el = t2, this.instance = e2, this.srcThumbnail = this.el.getAttribute("src"), this.srcset = this.el.getAttribute("srcset"), this.srcOriginal = a(this.el), this.rect = this.el.getBoundingClientRect(), this.translate = null, this.scale = null, this.styleOpen = null, this.styleClose = null;
        }, zoomIn: function() {
          var t2 = this.instance.options, e2 = t2.zIndex, s2 = t2.enableGrab, o2 = t2.transitionDuration, r2 = t2.transitionTimingFunction;
          this.translate = this.calculateTranslate(), this.scale = this.calculateScale(), this.styleOpen = { position: "relative", zIndex: e2 + 1, cursor: s2 ? n : i, transition: c + "\n        " + o2 + "s\n        " + r2, transform: "translate3d(" + this.translate.x + "px, " + this.translate.y + "px, 0px)\n        scale(" + this.scale.x + "," + this.scale.y + ")", height: this.rect.height + "px", width: this.rect.width + "px" }, this.el.offsetWidth, this.styleClose = l(this.el, this.styleOpen, true);
        }, zoomOut: function() {
          this.el.offsetWidth, l(this.el, { transform: "none" });
        }, grab: function(t2, e2, i2) {
          var n2 = k(), o2 = n2.x - t2, r2 = n2.y - e2;
          l(this.el, { cursor: s, transform: "translate3d(\n        " + (this.translate.x + o2) + "px, " + (this.translate.y + r2) + "px, 0px)\n        scale(" + (this.scale.x + i2) + "," + (this.scale.y + i2) + ")" });
        }, move: function(t2, e2, i2) {
          var n2 = k(), s2 = n2.x - t2, o2 = n2.y - e2;
          l(this.el, { transition: c, transform: "translate3d(\n        " + (this.translate.x + s2) + "px, " + (this.translate.y + o2) + "px, 0px)\n        scale(" + (this.scale.x + i2) + "," + (this.scale.y + i2) + ")" });
        }, restoreCloseStyle: function() {
          l(this.el, this.styleClose);
        }, restoreOpenStyle: function() {
          l(this.el, this.styleOpen);
        }, upgradeSource: function() {
          if (this.srcOriginal) {
            var t2 = this.el.parentNode;
            this.srcset && this.el.removeAttribute("srcset");
            var e2 = this.el.cloneNode(false);
            e2.setAttribute("src", this.srcOriginal), e2.style.position = "fixed", e2.style.visibility = "hidden", t2.appendChild(e2), setTimeout(function() {
              this.el.setAttribute("src", this.srcOriginal), t2.removeChild(e2);
            }.bind(this), 50);
          }
        }, downgradeSource: function() {
          this.srcOriginal && (this.srcset && this.el.setAttribute("srcset", this.srcset), this.el.setAttribute("src", this.srcThumbnail));
        }, calculateTranslate: function() {
          var t2 = k(), e2 = this.rect.left + this.rect.width / 2, i2 = this.rect.top + this.rect.height / 2;
          return { x: t2.x - e2, y: t2.y - i2 };
        }, calculateScale: function() {
          var t2 = this.el.dataset, e2 = t2.zoomingHeight, i2 = t2.zoomingWidth, n2 = this.instance.options, s2 = n2.customSize, o2 = n2.scaleBase;
          if (!s2 && e2 && i2) return { x: i2 / this.rect.width, y: e2 / this.rect.height };
          if (s2 && "object" === (void 0 === s2 ? "undefined" : v(s2))) return { x: s2.width / this.rect.width, y: s2.height / this.rect.height };
          var r2 = this.rect.width / 2, a2 = this.rect.height / 2, l2 = k(), h2 = { x: l2.x - r2, y: l2.y - a2 }, c2 = h2.x / r2, u2 = h2.y / a2, d2 = o2 + Math.min(c2, u2);
          if (s2 && "string" == typeof s2) {
            var f2 = i2 || this.el.naturalWidth, p2 = e2 || this.el.naturalHeight, y2 = parseFloat(s2) * f2 / (100 * this.rect.width), m2 = parseFloat(s2) * p2 / (100 * this.rect.height);
            if (d2 > y2 || d2 > m2) return { x: y2, y: m2 };
          }
          return { x: d2, y: d2 };
        } };
        function k() {
          var t2 = document.documentElement;
          return { x: Math.min(t2.clientWidth, window.innerWidth) / 2, y: Math.min(t2.clientHeight, window.innerHeight) / 2 };
        }
        function S(t2, e2, i2) {
          ["mousedown", "mousemove", "mouseup", "touchstart", "touchmove", "touchend"].forEach(function(n2) {
            o(t2, n2, e2[n2], i2);
          });
        }
        return function() {
          function i2(t2) {
            b(this, i2), this.target = Object.create(O), this.overlay = Object.create(g), this.handler = Object.create(p), this.body = document.body, this.shown = false, this.lock = false, this.released = true, this.lastScrollPosition = null, this.pressTimer = null, this.options = x({}, f, t2), this.overlay.init(this), this.handler.init(this);
          }
          return w(i2, [{ key: "listen", value: function(t2) {
            if ("string" == typeof t2) for (var i3 = document.querySelectorAll(t2), n2 = i3.length; n2--; ) this.listen(i3[n2]);
            else "IMG" === t2.tagName && (t2.style.cursor = e, o(t2, "click", this.handler.click), this.options.preloadImage && r(a(t2)));
            return this;
          } }, { key: "config", value: function(t2) {
            return t2 ? (x(this.options, t2), this.overlay.updateStyle(this.options), this) : this.options;
          } }, { key: "open", value: function(t2) {
            var e2 = this, i3 = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : this.options.onOpen;
            if (!this.shown && !this.lock) {
              var n2 = "string" == typeof t2 ? document.querySelector(t2) : t2;
              if ("IMG" === n2.tagName) {
                if (this.options.onBeforeOpen(n2), this.target.init(n2, this), !this.options.preloadImage) {
                  var s2 = this.target.srcOriginal;
                  null != s2 && (this.options.onImageLoading(n2), r(s2, this.options.onImageLoaded));
                }
                this.shown = true, this.lock = true, this.target.zoomIn(), this.overlay.insert(), this.overlay.fadeIn(), o(document, "scroll", this.handler.scroll), o(document, "keydown", this.handler.keydown), this.options.closeOnWindowResize && o(window, "resize", this.handler.resizeWindow);
                return o(n2, u, function t3() {
                  o(n2, u, t3, false), e2.lock = false, e2.target.upgradeSource(), e2.options.enableGrab && S(document, e2.handler, true), i3(n2);
                }), this;
              }
            }
          } }, { key: "close", value: function() {
            var e2 = this, i3 = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : this.options.onClose;
            if (this.shown && !this.lock) {
              var n2 = this.target.el;
              this.options.onBeforeClose(n2), this.lock = true, this.body.style.cursor = t, this.overlay.fadeOut(), this.target.zoomOut(), o(document, "scroll", this.handler.scroll, false), o(document, "keydown", this.handler.keydown, false), this.options.closeOnWindowResize && o(window, "resize", this.handler.resizeWindow, false);
              return o(n2, u, function t2() {
                o(n2, u, t2, false), e2.shown = false, e2.lock = false, e2.target.downgradeSource(), e2.options.enableGrab && S(document, e2.handler, false), e2.target.restoreCloseStyle(), e2.overlay.remove(), i3(n2);
              }), this;
            }
          } }, { key: "grab", value: function(t2, e2) {
            var i3 = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : this.options.scaleExtra, n2 = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : this.options.onGrab;
            if (this.shown && !this.lock) {
              var s2 = this.target.el;
              this.options.onBeforeGrab(s2), this.released = false, this.target.grab(t2, e2, i3);
              return o(s2, u, function t3() {
                o(s2, u, t3, false), n2(s2);
              }), this;
            }
          } }, { key: "move", value: function(t2, e2) {
            var i3 = arguments.length > 2 && void 0 !== arguments[2] ? arguments[2] : this.options.scaleExtra, n2 = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : this.options.onMove;
            if (this.shown && !this.lock) {
              this.released = false, this.body.style.cursor = s, this.target.move(t2, e2, i3);
              var r2 = this.target.el;
              return o(r2, u, function t3() {
                o(r2, u, t3, false), n2(r2);
              }), this;
            }
          } }, { key: "release", value: function() {
            var e2 = this, i3 = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : this.options.onRelease;
            if (this.shown && !this.lock) {
              var n2 = this.target.el;
              this.options.onBeforeRelease(n2), this.lock = true, this.body.style.cursor = t, this.target.restoreOpenStyle();
              return o(n2, u, function t2() {
                o(n2, u, t2, false), e2.lock = false, e2.released = true, i3(n2);
              }), this;
            }
          } }]), i2;
        }();
      });
    }
  });

  // <stdin>
  var import_zooming_v2_1_1_min = __toESM(require_zooming_v2_1_1_min());
  document.addEventListener("DOMContentLoaded", function() {
    let bgColor;
    if (localStorage.theme === "dark" || !("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      bgColor = "#333";
    } else {
      bgColor = "#fff";
    }
    zooming = new import_zooming_v2_1_1_min.default({
      transitionDuration: 0.2,
      bgColor
    });
    zooming.listen("#content img");
    const dark_mode_btn = document.getElementById("dark_mode_btn");
    const light_mode_btn = document.getElementById("light_mode_btn");
    dark_mode_btn.addEventListener("click", function() {
      zooming.config({ bgColor: "#333" });
    });
    light_mode_btn.addEventListener("click", function() {
      zooming.config({ bgColor: "#fff" });
    });
  });
})();
