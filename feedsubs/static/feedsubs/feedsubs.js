function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sendRequest(current)
{
    var type = current.dataset.type;
    var pk = current.dataset.id;
    var action = current.dataset.action;
    var url = current.dataset.url;
    var method = 'POST';

    if (url === undefined) {
        if (pk === "") {
            url = "/" + type + "/" + action;
        } else {
            url = "/" + type + "/" + pk + "/" + action;
        }
    }

    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {

        // Only run if the request is complete
        if (xhr.readyState !== 4) return;

        // Process our return data
        if (xhr.status >= 200 && xhr.status < 300) {
            if (action === "star") {
                current.classList.add("is-warning", "is-selected");
                current.dataset.action = "unstar";
            } else if (action === "unstar") {
                current.classList.remove("is-warning", "is-selected");
                current.dataset.action = "star";
            } else if (action === "read") {
                current.classList.add("is-success", "is-selected");
                current.dataset.action = "unread";
            } else if (action === "unread") {
                current.classList.remove("is-success", "is-selected");
                current.dataset.action = "read";
            } else if (action === "unsubscribe") {
                current.setAttribute("disabled", true);
                location.reload(true);
            } else if (action === "subscribe") {
                current.setAttribute("disabled", true);
                location.reload(true);
            } else if (action === "read-all") {
                current.setAttribute("disabled", true);
                var el = document.querySelectorAll('[data-action="read"]');
                for (var i = 0; i < el.length; i++) {
                    el[i].classList.add("is-success", "is-selected");
                    el[i].dataset.action = "unread";
                }
            }
        }

    };

    xhr.open(method, url);
    xhr.setRequestHeader('Cache-Control', 'no-cache');
    if (!csrfSafeMethod(method) && !xhr.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
    xhr.send();
}

document.addEventListener('click', function (event) {

    var target = event.target;

	if (target.closest('.notification > button.delete')) {
        target.parentNode.classList.add('is-hidden');
	}

	if (target.matches('.navbar-burger')) {
        var associated = document.getElementById(target.dataset.target);

        // Toggle the class on both the "navbar-burger" and the "navbar-menu"
        target.classList.toggle('is-active');
        associated.classList.toggle('is-active');
    }

	if (target.closest('#edit-tags-button')) {
        document.getElementById('show-tags-box').classList.add("is-hidden");
        document.getElementById('edit-tags-box').classList.remove("is-hidden");
    }

	if (target.closest('[data-action]')) {
	    sendRequest(target.closest('[data-action]'));
    }


}, false);
