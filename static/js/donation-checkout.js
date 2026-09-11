(function () {
  "use strict";

  var form = document.getElementById("flutterwavePaymentForm");
  var button = document.getElementById("payNowButton");
  var status = document.getElementById("donationStatus");

  if (!form || !button || !status) return;

  function showStatus(message, type) {
    status.textContent = message;
    status.className = "as-form-status is-visible " + (type || "");
  }

  function setButtonBusy(isBusy) {
    button.disabled = isBusy;
    button.innerHTML = isBusy
      ? 'Opening checkout… <i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>'
      : 'Continue to payment <i class="fa-solid fa-arrow-right" aria-hidden="true"></i>';
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;

    if (typeof window.FlutterwaveCheckout !== "function") {
      showStatus(
        "The payment window could not be loaded. Check your connection or use the bank-transfer details on this page.",
        "is-error"
      );
      return;
    }

    var amount = Number(document.getElementById("donation_amount").value);
    if (!Number.isFinite(amount) || amount <= 0) {
      showStatus("Enter a valid gift amount greater than zero.", "is-error");
      return;
    }

    var completed = false;
    var referencePrefix = form.dataset.referencePrefix || "gift";
    var checkout;

    setButtonBusy(true);
    showStatus("Opening Flutterwave’s secure payment window…", "");

    checkout = window.FlutterwaveCheckout({
      public_key: "FLWPUBK-eabfcd297464d04dd146e66a866942d6-X",
      tx_ref: referencePrefix + "_" + Date.now() + "_" + Math.floor(Math.random() * 100000),
      amount: amount,
      currency: document.getElementById("currency").value,
      customer: {
        email: document.getElementById("donor_email").value.trim(),
        phone_number: document.getElementById("phone").value.trim(),
        name: document.getElementById("donor_name").value.trim()
      },
      meta: {
        gift_message: document.getElementById("donation_message").value.trim(),
        gift_purpose: form.dataset.checkoutDescription || "Ministry gift"
      },
      customizations: {
        title: form.dataset.checkoutTitle || "Awakening Saints",
        description: form.dataset.checkoutDescription || "Voluntary ministry gift",
        logo: new URL(form.dataset.logoUrl || "/static/assets/images/logo.png", window.location.origin).href
      },
      callback: function (payment) {
        completed = true;
        setButtonBusy(false);
        showStatus(
          "Your payment was submitted to Flutterwave. Check your email for confirmation. Transaction ID: " + payment.transaction_id,
          "is-success"
        );
        if (checkout && typeof checkout.close === "function") checkout.close();
      },
      onclose: function (incomplete) {
        setButtonBusy(false);
        if (!completed && incomplete) {
          showStatus("Payment was not completed. No gift was submitted; you may try again whenever you are ready.", "is-error");
        }
      }
    });
  });
}());
