document.addEventListener("DOMContentLoaded", function() {
  console.log("Hello from hide_alerts controller")

  let alerts = document.querySelectorAll('.alert');
    for (let alert of alerts) {
        // Check if the alert is currently displayed
        if (alert.style.display !== 'none') {

            // Hide it after 3 seconds
            setTimeout(() => {
                alert.style.display = 'none';
            }, 4000);
        }
    }
});
