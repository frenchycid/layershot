import Foundation
@testable import LayerShotApp

// Entry point: run all tests
print("Starting test suite...")
AppStateTests().runTests()
PipelineRunnerTests().runTests()
print("\n=== All tests completed ===")
