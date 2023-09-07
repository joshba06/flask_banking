document.addEventListener("DOMContentLoaded", function() {
  const showTransactionsFieldButton = document.getElementById("show-new-transaction-field");
  const cancelAddingTransactionButton = document.getElementById("btn-cancel-add-transaction");
  const newTransactionDiv = document.getElementById("new-transaction-div");

  // Add click event listener to "Add Transaction" button
  showTransactionsFieldButton.addEventListener("click", function(event) {
      event.preventDefault();
      // cancelAddingTransactionButton.style.display = "inline";
      newTransactionDiv.style.display = "flex";
      newTransactionDiv.classList.add("new-transaction-form")
  });

  // Add click event listener to "Cancel" button
  // cancelAddingTransactionButton.addEventListener("click", function(event) {
  //     event.preventDefault();
  //     addTransactionButton.style.display = "block";
  //     cancelAddingTransactionButton.style.display = "none";
  //     newTransactionForm.style.display = "none";
  // });

});
