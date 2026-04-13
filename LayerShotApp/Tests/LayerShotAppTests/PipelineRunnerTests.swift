import Foundation
@testable import LayerShotApp

final class PipelineRunnerTests {
    var testCount = 0
    var passCount = 0
    var failCount = 0

    func runTests() {
        print("\n=== Running PipelineRunnerTests ===")
        test_build_analyze_command()
        test_build_prompt_command()
        test_build_generate_command_includes_products()
        test_build_review_command()

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

    private func assertArrayEqual(_ a: [String], _ b: [String], _ message: String) {
        assert(a == b, message)
    }

    func test_build_analyze_command() {
        let runner = PipelineRunner(
            pythonPath: "/usr/bin/python3",
            projectPath: "/tmp/layershot"
        )
        let moodboard = URL(fileURLWithPath: "/tmp/moodboard")
        let output = URL(fileURLWithPath: "/tmp/analysis.json")
        let cmd = runner.buildAnalyzeCommand(moodboardPath: moodboard, outputPath: output)
        assertArrayEqual(cmd, [
            "/usr/bin/python3",
            "/tmp/layershot/main.py",
            "analyze",
            "--moodboard", "/tmp/moodboard",
            "--output", "/tmp/analysis.json"
        ], "test_build_analyze_command")
    }

    func test_build_prompt_command() {
        let runner = PipelineRunner(
            pythonPath: "/usr/bin/python3",
            projectPath: "/tmp/layershot"
        )
        let analysis = URL(fileURLWithPath: "/tmp/analysis.json")
        let output = URL(fileURLWithPath: "/tmp/prompt.json")
        let cmd = runner.buildPromptCommand(analysisPath: analysis, outputPath: output)
        assertArrayEqual(cmd, [
            "/usr/bin/python3",
            "/tmp/layershot/main.py",
            "prompt",
            "--analysis", "/tmp/analysis.json",
            "--output", "/tmp/prompt.json"
        ], "test_build_prompt_command")
    }

    func test_build_generate_command_includes_products() {
        let runner = PipelineRunner(
            pythonPath: "/usr/bin/python3",
            projectPath: "/tmp/layershot"
        )
        let prompt = URL(fileURLWithPath: "/tmp/prompt.json")
        let output = URL(fileURLWithPath: "/tmp/outputs")
        let products = [
            Product(name: "bag", color: "black"),
            Product(name: "shoe", color: "white")
        ]
        let cmd = runner.buildGenerateCommand(promptPath: prompt, products: products, outputDir: output)
        assert(cmd.contains("generate"), "test_build_generate_command_includes_products: contains generate")
        assert(cmd.contains("--products"), "test_build_generate_command_includes_products: contains --products")
        assert(cmd.contains("bag:black"), "test_build_generate_command_includes_products: contains bag:black")
        assert(cmd.contains("shoe:white"), "test_build_generate_command_includes_products: contains shoe:white")
    }

    func test_build_review_command() {
        let runner = PipelineRunner(
            pythonPath: "/usr/bin/python3",
            projectPath: "/tmp/layershot"
        )
        let images = URL(fileURLWithPath: "/tmp/outputs")
        let analysis = URL(fileURLWithPath: "/tmp/analysis.json")
        let report = URL(fileURLWithPath: "/tmp/report.json")
        let cmd = runner.buildReviewCommand(imagesDir: images, analysisPath: analysis, outputPath: report)
        assert(cmd.contains("review"), "test_build_review_command: contains review")
        assert(cmd.contains("--images"), "test_build_review_command: contains --images")
        assert(cmd.contains("--analysis"), "test_build_review_command: contains --analysis")
        assert(cmd.contains("--output"), "test_build_review_command: contains --output")
    }
}
