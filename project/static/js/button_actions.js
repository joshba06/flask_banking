document.addEventListener("DOMContentLoaded", function() {
  const showTransactionsFieldButton = document.getElementById("show-new-transaction-field");
  const cancelAddingTransactionButton = document.getElementById("btn-cancel-add-transaction");
  const newTransactionDiv = document.getElementById("new-transaction-div");

  // Add click event listener to "Add Transaction" button
  showTransactionsFieldButton.addEventListener("click", function(event) {
      event.preventDefault();
      newTransactionDiv.style.display = "block";
      newTransactionDiv.classList.add("new-transaction-form")
  });

  // Add click event listener to "Cancel" button
  cancelAddingTransactionButton.addEventListener("click", function(event) {
      event.preventDefault();
      newTransactionDiv.style.display = "none";
  });

});

// SUBACCOUNT TRANSFER: Remove active account from dropdown
document.addEventListener("DOMContentLoaded", function() {
  var selectElement = document.getElementById('new-transaction-recipient');
  var accountNameDiv = document.querySelector('#active-account .account-title')
  var accountIbanDiv = document.querySelector('#active-account .account-iban')

  // If the ibanDiv exists, return its text content
  if (accountNameDiv && accountIbanDiv) {
    const accountTitle =  accountNameDiv.textContent.trim();
    const accountIban = accountIbanDiv.textContent.trim();
    console.log(`Found account title: ${accountTitle} and iban: ${accountIban}`)

    // Loop over the options in the select element
    const searchTerm = `${accountTitle} (${accountIban.slice(0, 4)}...${accountIban.slice(-2)})`
    console.log(`Search term ${searchTerm}`)
    for (var i = 0; i < selectElement.options.length; i++) {
      if (selectElement.options[i].value === searchTerm) {
          selectElement.removeChild(selectElement.options[i]);
          console.log("Removed active account from dropdown")
          break; // Exit the loop once the option is found and removed
      }
    }
  }
  else {
    console.log(`Couldnt find account title`)
  }

});


// Form submission fields
'use strict';

function initValidation() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');

    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
        form.addEventListener('submit', function(event) {

          // When the submit button of the STANDARD PAYMENT form is pressed and "CATEGORY" exists, display error message
          if ((event.currentTarget.className.includes("form-standard-payment")) && (document.getElementById("new-transaction-category").value === "Category")) {
            console.log("STANDARD PAYMENT")
            document.getElementById("new-transaction-category").setCustomValidity("Invalid field.")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
          else if ((event.currentTarget.className.includes("form-subaccount-transfer")) && (document.getElementById("new-transaction-recipient").value === "Recipient")){
            console.log("SUBACCOUNT TRANSFER")
            document.getElementById("new-transaction-recipient").setCustomValidity("Invalid field.")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
        }, false);
    });
}

// Ensure the DOM content is loaded before the script runs
document.addEventListener('DOMContentLoaded', initValidation);
