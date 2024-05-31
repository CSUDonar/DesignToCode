js_code = """
<script>
    (function(history){
        var pushState = history.pushState;
        var replaceState = history.replaceState;

        history.pushState = function(state) {
            if (typeof history.onpushstate == "function") {
                history.onpushstate({state: state});
            }
            return pushState.apply(history, arguments);
        };

        history.replaceState = function(state) {
            if (typeof history.onreplacestate == "function") {
                history.onreplacestate({state: state});
            }
            return replaceState.apply(history, arguments);
        };

        window.onpopstate = function(event) {
            history.go(1);
        };

        window.history.pushState(null, "", window.location.href);

        window.onbeforeunload = function() {
            return "Are you sure you want to leave?";
        };
    })(window.history);
</script>
"""