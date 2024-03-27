
function newpage() {
    var domainName = window.location.hostname;


    var inputValue = document.getElementById("inputText").value;
    if (/^\d+$/.test(inputValue)) {
        window.open("http://"+domainName+":" + inputValue, "_blank");
    }
    else {
        window.open("https://" + inputValue + ".hoao.fun", "_blank");
    }
}
document.getElementById("inputText").addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {
        newpage();
    }
});




