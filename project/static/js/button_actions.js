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
// document.addEventListener("DOMContentLoaded", function() {
//   var selectElement = document.getElementById('new-transaction-recipient');
//   var accountNameDiv = document.querySelector('#active-account .account-title')
//   var accountIbanDiv = document.querySelector('#active-account .account-iban')

//   // If the ibanDiv exists, return its text content
//   if (accountNameDiv && accountIbanDiv) {
//     const accountTitle =  accountNameDiv.textContent.trim();
//     const accountIban = accountIbanDiv.textContent.trim();
//     console.log(`Found account title: ${accountTitle} and iban: ${accountIban}`)

//     // Loop over the options in the select element
//     const searchTerm = `${accountTitle} (${accountIban.slice(0, 4)}...${accountIban.slice(-2)})`
//     console.log(`Search term ${searchTerm}`)
//     for (var i = 0; i < selectElement.options.length; i++) {
//       if (selectElement.options[i].value === searchTerm) {
//           selectElement.removeChild(selectElement.options[i]);
//           console.log("Removed active account from dropdown")
//           break; // Exit the loop once the option is found and removed
//       }
//     }
//   }
//   else {
//     console.log(`Couldnt find account title`)
//   }

// });



// Add custom invalid field messages_________________________________________________________

// New Account form
const newAccountTitle = document.getElementById("newAccountTitleInput");
newAccountTitle.addEventListener("input", function(e){
  newAccountTitle.setCustomValidity('');
  if ((newAccountTitle.value.length >= 3) && (/^[0-9]/.test(newAccountTitle.value))) {
    newAccountTitle.setCustomValidity('The account title cannot start with a digit.');
  }

});
const editAccountTitle = document.getElementById("editAccountTitleInput");
editAccountTitle.addEventListener("input", function(e){
  editAccountTitle.setCustomValidity('');
  if ((editAccountTitle.value.length >= 3) && (/^[0-9]/.test(editAccountTitle.value))) {
    editAccountTitle.setCustomValidity('The account title cannot start with a digit.');
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
        if (event.currentTarget.className.includes("form-standard-payment")) {
          if (document.getElementById("new-transaction-category").value === "Category"){
            document.getElementById("new-transaction-category").setCustomValidity("Please select a valid category.")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
          if (document.getElementById("new-transaction-amount").value === "0") {
            document.getElementById("new-transaction-amount").setCustomValidity("Amount cannot be zero (may be negative or positive)")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
          const transactionDescription = document.getElementById("new-transaction-description").value.trim();
          if ( transactionDescription.length < 3) {
            document.getElementById("new-transaction-description").setCustomValidity("Description too short (consider whitespaces)")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
        }
        else if (event.currentTarget.className.includes("form-subaccount-transfer")) {
          if (document.getElementById("new-transfer-recipient").value === "Recipient"){
            document.getElementById("new-transfer-recipient").setCustomValidity("Invalid field.")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
          const transfernDescription = document.getElementById("new-transfer-description").value.trim();
          if ( transfernDescription.length < 3) {
            document.getElementById("new-transfer-description").setCustomValidity("Description too short (consider whitespaces)")
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
          }
        }

      }, false);
  });
  // Reset the dropdown's validity when its value changes
  document.getElementById("new-transaction-category").addEventListener('change', function() {
    if (this.value !== "Category") {
        this.setCustomValidity("");
    }
  });
  document.getElementById("new-transfer-recipient").addEventListener('change', function() {
    if (this.value !== "Recipient") {
        this.setCustomValidity("");
    }
  });
  document.getElementById("new-transaction-amount").addEventListener('input', function() {
    if (this.value !== "0") {
        this.setCustomValidity("");
    }
  });
  document.getElementById("new-transaction-description").addEventListener('input', function() {
    if (this.value.trim().length >= 3) {
        this.setCustomValidity("");
    }
  });
  document.getElementById("new-transfer-description").addEventListener('input', function() {
    if (this.value.trim().length >= 3) {
        this.setCustomValidity("");
    }
  });
}



// Ensure the DOM content is loaded before the script runs
document.addEventListener('DOMContentLoaded', initValidation);
