document.addEventListener("DOMContentLoaded", () => {
  $("#autocomplete").autocomplete({
      source: unique_descriptions
  });
});
