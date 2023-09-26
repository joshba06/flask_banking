// New account form
document.getElementById('showNewAccountBtn').addEventListener('click', function() {
  document.getElementById('overlay_new_account').style.display = 'block';
});

document.getElementById('closeNewAccountBtn').addEventListener('click', function() {
  document.getElementById('overlay_new_account').style.display = 'none';
});

// Edit account form
document.getElementById('showEditAccountBtn').addEventListener('click', function() {
  document.getElementById('overlay_edit_account').style.display = 'block';
});
document.getElementById('closeEditAccountBtn').addEventListener('click', function() {
  document.getElementById('overlay_edit_account').style.display = 'none';
});


// Delete account form
document.getElementById('delete-account-btn').addEventListener('click', function(event) {

  const userResponse = confirm("Are you sure you want to delete this account?");
  if (userResponse) {
    console.log("Deleting account")
  }
  else {
    event.preventDefault();
  }
});
