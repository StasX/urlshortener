const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

let request, success, failure, reloads = 0;
const $ = () => ({ ready() {} });
$.ajax = (options) => {
    request = options;
    return {
        done(callback) { success = callback; return this; },
        fail(callback) { failure = callback; return this; },
    };
};
const context = vm.createContext({ $, document: {}, location: { reload() { reloads++; } } });
vm.runInContext(fs.readFileSync(require("node:path").join(__dirname, "../src/static/js/main.js"), "utf8"), context);
const button = { prop(name, value) { assert.equal(name, "disabled"); this.disabled = value; } };
const error = { text(value) { this.message = value; } };

context.removeUrl("id/with slash", button, error);
assert.equal(request.url, "/urls/id%2Fwith%20slash");
assert.equal(request.method, "DELETE");
assert.equal(button.disabled, true);
assert.equal(error.message, "");
success();
assert.equal(reloads, 1);

context.removeUrl("id", button, error);
failure({ responseJSON: { error: "Authentication required." } });
assert.equal(error.message, "Authentication required.");
assert.equal(button.disabled, false);
assert.equal(reloads, 1);
failure({});
assert.equal(error.message, "Could not remove the link. Please try again.");
console.log("Deletion client checks passed");
