import Foundation

public struct PipelineRunner {
    public let pythonPath: String
    public let projectPath: String

    public init(pythonPath: String, projectPath: String) {
        self.pythonPath = pythonPath
        self.projectPath = projectPath
    }

    public func buildAnalyzeCommand(moodboardPath: URL, outputPath: URL) -> [String] {
        [pythonPath, "\(projectPath)/main.py", "analyze",
         "--moodboard", moodboardPath.path,
         "--output", outputPath.path]
    }

    public func buildPromptCommand(analysisPath: URL, outputPath: URL) -> [String] {
        [pythonPath, "\(projectPath)/main.py", "prompt",
         "--analysis", analysisPath.path,
         "--output", outputPath.path]
    }

    public func buildGenerateCommand(promptPath: URL, products: [Product], outputDir: URL) -> [String] {
        var args = [pythonPath, "\(projectPath)/main.py", "generate",
                    "--prompt", promptPath.path,
                    "--output", outputDir.path,
                    "--products"]
        args += products.map { $0.cliArgument }
        return args
    }

    public func buildReviewCommand(imagesDir: URL, analysisPath: URL, outputPath: URL) -> [String] {
        [pythonPath, "\(projectPath)/main.py", "review",
         "--images", imagesDir.path,
         "--analysis", analysisPath.path,
         "--output", outputPath.path]
    }

    /// Run a shell command, streaming output lines to `outputHandler` on MainActor.
    /// Returns full stdout on success; throws `PipelineError` on failure.
    @discardableResult
    public func run(command: [String], outputHandler: @MainActor @escaping (String) -> Void) async throws -> String {
        try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            let outPipe = Pipe()
            let errPipe = Pipe()

            process.executableURL = URL(fileURLWithPath: command[0])
            process.arguments = Array(command.dropFirst())
            process.standardOutput = outPipe
            process.standardError = errPipe

            var fullOutput = ""

            outPipe.fileHandleForReading.readabilityHandler = { handle in
                let data = handle.availableData
                guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
                fullOutput += text
                Task { await outputHandler(text) }
            }

            errPipe.fileHandleForReading.readabilityHandler = { handle in
                let data = handle.availableData
                guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
                Task { await outputHandler("[ERR] " + text) }
            }

            do {
                try process.run()
                process.waitUntilExit()
                outPipe.fileHandleForReading.readabilityHandler = nil
                errPipe.fileHandleForReading.readabilityHandler = nil

                if process.terminationStatus == 0 {
                    continuation.resume(returning: fullOutput)
                } else {
                    continuation.resume(throwing: PipelineError.processFailure(Int(process.terminationStatus)))
                }
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }
}

public enum PipelineError: LocalizedError {
    case processFailure(Int)
    case noMoodboard
    case noProducts

    public var errorDescription: String? {
        switch self {
        case .processFailure(let code):
            return "Processus échoué (code \(code))"
        case .noMoodboard:
            return "Aucun moodboard sélectionné"
        case .noProducts:
            return "Aucun produit ajouté"
        }
    }
}
