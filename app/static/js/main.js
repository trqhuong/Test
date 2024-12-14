function loginRequired() {
    let popup = document.querySelector(".popup")
    popup.innerHTML = `
        <!-- The Modal -->
        <div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
        
              <!-- Modal Header -->
              <div class="modal-header">
                <h4 class="modal-title">Please Login</h4>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
        
              <!-- Modal body -->
              <div class="modal-body">
                You must be logged in to book your hotel.
              </div>
        
              <!-- Modal footer -->
              <div class="modal-footer">
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                    <a href="/login" class="text-white">Login</a>
                </button>
                <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
              </div>
        
            </div>
          </div>
        </div>`
    var myModal = new bootstrap.Modal(document.getElementById('myModal'));
    myModal.show();
}

let count = 1;

function addCustomer() {
    if(count <= 2) {
        count += 1
        customer = document.querySelector(".list-customer");
        customer.insertAdjacentHTML("beforeend", `
        <div class="col-md-6 mb-3 customer-item">
            <div class="p-3 customer-update" style="background: #D9D9D9;">
                <div class="row">
                    <h6 class="col-md-9"">Customer ${count}:</h6>
                    <button type="button" class="btn btn-danger col-md-3 delete-customer">Delete</button>
                </div>
                <div class="mb-2">
                    <label for="name" class="form-label">Name:</label>
                    <input type="text" id="name${count}" class="form-control name" name="name" required>
                </div>
                <div class="mb-2">
                    <label for="id" class="form-label">Identification number:</label>
                    <input type="text" id="id${count}" class="form-control id" name="identification_card" required>
                </div>
                <div style="text-align: left">
                    <p>Chosse Customer Type</p>
                    <select id="type${count}" class="form-select rounded-0" name="customer_type"
                            style="height: 40px;">
                        <option value="Domestic">Domestic</option>
                        <option value="Foreign">Foreign</option>
                    </select>
                </div>
            </div>
        </div>
        `)
    } else {
        let info = document.querySelector(".info")
        info.style.display = "block";
    }
    var myModal = new bootstrap.Modal(document.getElementById('myModal'));
    myModal.show();
}

//======================Delete Customer==================================
let deleteCustomer = document.querySelector(".list-customer");

deleteCustomer.addEventListener("click", function (event) {
    if(event.target.classList.contains("delete-customer")) {
        event.target.closest(".customer-item").remove();
        count--;
        updateCustomer();
    }
});
//======================End Delete Customer==================================

function updateCustomer() {
    listCustomer = document.querySelectorAll(".customer-item")
    listCustomer.forEach((item, index) => {
        if(index > 0) {//Bỏ customer đầu mặc định đã đăng kí tài khoản
            customerNumber = index + 1;
            item.querySelector(".row > h6").textContent = `Customer ${customerNumber}`;
        }
    })
}

//============================================================================

window.onload = function () {
    let checkin = document.getElementById("check-in")
    let checkout = document.getElementById("check-out")
    console.log("1")
    checkin.addEventListener("change", saveDate)
    checkout.addEventListener("change", saveDate)

    function saveDate() {
        checkin = document.getElementById("check-in");
        checkout = document.getElementById("check-out");
        console.log(checkin.value);
        console.log(checkout.value);

        navigator.sendBeacon("/save_date", JSON.stringify({
            checkin: checkin.value,
            checkout: checkout.value,
        }))
    }
}
//==================================Auto Fill====================================
function autoFill(name, identification_card, customer_type) {
    let checked = document.querySelector(".cb")

    let nameCus = document.getElementById("name");
    let id = document.getElementById("id");
    let type = document.getElementById("type");

    if (!checked.checked) {
        nameCus.value = name;
        nameCus.readOnly = true;

        id.value = identification_card;
        id.readOnly = true;

        type.innerHTML = `<option value="${customer_type}">${customer_type}</option>`;
    } else {
        nameCus.value = '';
        nameCus.readOnly = false;

        id.value = '';
        id.readOnly = false;

        type.innerHTML = `<option value="Domestic">Domestic</option>
                            <option value="Foreign">Foreign</option>`;
    }
}