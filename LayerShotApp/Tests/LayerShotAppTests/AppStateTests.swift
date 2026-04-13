import Foundation
@testable import LayerShotApp

// Simple test runner since XCTest is problematic on Swift macOS
final class AppStateTests {
    var testCount = 0
    var passCount = 0
    var failCount = 0

    func runTests() {
        print("\n=== Running AppStateTests ===")
        test_product_cli_argument()
        test_appstate_add_product()
        test_appstate_remove_product()
        test_generated_image_parses_filename()
        test_generated_image_rejects_bad_filename()

        print("\nResults: \(passCount) passed, \(failCount) failed out of \(testCount)")
        if failCount > 0 {
            exit(1)
        }
    }

    private func assert(_ condition: Bool, _ message: String) {
        testCount += 1
        if condition {
            passCount += 1
            print("✓ \(message)")
        } else {
            failCount += 1
            print("✗ \(message)")
        }
    }

    func test_product_cli_argument() {
        let p = Product(name: "handbag", color: "black")
        assert(p.cliArgument == "handbag:black", "test_product_cli_argument")
    }

    func test_appstate_add_product() {
        let state = AppState()
        state.addProduct(name: "bag", color: "red")
        assert(state.products.count == 1, "test_appstate_add_product: count")
        assert(state.products[0].name == "bag", "test_appstate_add_product: name")
    }

    func test_appstate_remove_product() {
        let state = AppState()
        state.addProduct(name: "bag", color: "red")
        state.removeProduct(at: 0)
        assert(state.products.count == 0, "test_appstate_remove_product")
    }

    func test_generated_image_parses_filename() {
        let url = URL(fileURLWithPath: "/tmp/handbag_black_wide_1.png")
        let img = GeneratedImage.from(url: url)
        assert(img != nil, "test_generated_image_parses_filename: not nil")
        assert(img?.productName == "handbag", "test_generated_image_parses_filename: productName")
        assert(img?.color == "black", "test_generated_image_parses_filename: color")
        assert(img?.view == "wide", "test_generated_image_parses_filename: view")
        assert(img?.variant == 1, "test_generated_image_parses_filename: variant")
    }

    func test_generated_image_rejects_bad_filename() {
        let url = URL(fileURLWithPath: "/tmp/bad.png")
        let img = GeneratedImage.from(url: url)
        assert(img == nil, "test_generated_image_rejects_bad_filename")
    }
}

// Entry point for tests
AppStateTests().runTests()
