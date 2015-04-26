(function ($) {
    "use strict";
    /*global document, window, jQuery, console */

    if (window.Select2 === undefined) {
        return;
    }

    if (window.Select2Custom !== undefined) {
        return;
    }

    function findResult(results, matcher) {
        if (!results || !results.length) { return null; }
        var _l = results.length;
        var match = null;
        for (var i=0; i<_l; i++) {
            match = matcher(results[i]);
            if (match) { return match; }
            if (results[i].children) {
                return findResult(results[i].children, matcher);
            }
        }
    }
    var defaults = $.fn.select2.defaults;

    function prepareOpts(opts) {
        var stripDiacritics = window.Select2.util.stripDiacritics;
        var markMatch = window.Select2.util.markMatch;
        // If autoTag enabled, ensure that various related options are defined
        if (opts.autoTag) {
            if (!opts.formatNoMatches) {
                opts.formatNoMatches = "No matches";
            }
            if (!opts.placeholder) {
                opts.placeholder = "Select or type in a value";
            }
            if (opts.allowClear === undefined) {
              opts.allowClear = true;
            }
            if (!opts.createSearchChoice) {
                opts.createSearchChoice = function(term, results) {
                    var exactMatch = findResult(results, function(result) {
                        if (defaults.matcher(result.text, term)) {
                            return result;
                        }
                    });
                    // console.log("createSearchChoice: " + term + ", " + results[0].text);
                    if (!exactMatch) {
                        return { 'id': term, 'text': term, 'tag': true };
                    }
                };
            }
            if (!opts.nextSearchTerm) {
                opts.nextSearchTerm = function (obj, term) {
                    // console.log("nextSearchTerm: " + obj + ", " + term);
                    if (obj) {
                        return obj.text;
                    } else {
                        return term;
                    }
                };
            }
            if (!opts.formatResult) {
                  opts.formatResult = function (result, container, query, escapeMarkup) {
                      if (!result.id) {
                          return result.text;
                      }
                      if (result.tag) {
                          var markup = [result.text];
                          if (opts.autoTagHelp) {
                              markup.push('<div class="select2-tag-help">');
                              markup.push(opts.autoTagHelp);
                              markup.push('</div>');
                          }
                          return markup.join('');
                      }
                      return defaults.formatResult(result, container, query, escapeMarkup);
                  };
            }
        }
        // Use createSearchChoice to generate initSelection if appropriate
        if (opts.data && opts.createSearchChoice && !opts.initSelection) {
            opts.initSelection = function(element, callback) {
                // Look for current value as an id, otherwise create a search choice
                var id = $(element).val();
                var data = opts.data.results || opts.data;
                var match = findResult(data, function(result) {
                    if (result.id && result.id == id) {
                        return result;
                    }
                });
                // console.log("initSelection: " + id + ", " + match);
                if (!match) {
                    match = opts.createSearchChoice(id);
                }
                if ($.isFunction(callback)) {
                    callback(match);
                }
            };
        }
        if (opts.data && opts.autoTag) {
            var data = opts.data.results || opts.data;
            if (data && data[0] && !data[0].children) {
                var groupName = opts.autoTagMatchGroup || "Suggestions";
                opts.data = { results: [{text: groupName, children: data}]};
            }
        }
        return opts;
    }

    window.Select2Custom = {
        'prepareOpts': prepareOpts
    };

}(jQuery));
