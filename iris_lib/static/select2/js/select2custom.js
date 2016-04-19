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
            // Show message when no matches
            if (!opts.formatNoMatches) {
                opts.formatNoMatches = "No matches";
            }
            // Show placeholder message
            if (!opts.placeholder) {
                opts.placeholder = "Select or type in a value";
            }
            // Allow value to be cleared
            if (opts.allowClear === undefined) {
              opts.allowClear = true;
            }
            // Create a dynamic search result for a given input
            if (!opts.createSearchChoice) {
                opts.createSearchChoice = function(term, results) {
                    // Check if the search term exactly matches anything
                    // Note that this basically means rerunning the search
                    var exactMatch = findResult(results, function(result) {
                        if (defaults.matcher(result.text, term)) {
                            return result;
                        }
                    });
                    // console.log("createSearchChoice: " + term + ", " + results[0].text);
                    // If no exact match, offer a tag based on the input
                    if (!exactMatch) {
                        return { 'id': term, 'text': term, 'tag': true };
                    }
                };
            }
            // Generate a search term for a given result
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
            // Format a matching result
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
        // This is typically when the page loads, the field has a value (eg. an object id) that
        // needs to be turned into a search result.
        if (opts.data && opts.createSearchChoice && !opts.initSelection) {
            opts.initSelection = function(element, callback) {
                // Try to match the field value against the id of each item
                var id = $(element).val();
                var data = opts.data.results || opts.data;
                var match = findResult(data, function(result) {
                    if (result.id && result.id == id) {
                        return result;
                    }
                });
                // console.log("initSelection: " + id + ", " + match);
                // If nothing matched, treat the value as though the user had typed it in
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
        // If no sorting specified, sort 0-index matches highest
        if (!opts.sortResults) {
            opts.sortResults = function(results, container, query) {
                if (query.term) {
                    return results.sort(function(a, b) {
                        var indexa = a.text.toUpperCase().indexOf(query.term.toUpperCase());
                        var indexb = b.text.toUpperCase().indexOf(query.term.toUpperCase());
                        if (indexa == 0 && indexb != 0) { return -1; }
                        else if (indexa != 0 && indexb == 0) { return 1; }
                        else { return 0; }
                    });
                }
                return results;
            };
        }
        return opts;
    }

    window.Select2Custom = {
        'prepareOpts': prepareOpts
    };

}(jQuery));
