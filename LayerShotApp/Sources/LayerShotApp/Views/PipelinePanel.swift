import SwiftUI

public struct PipelinePanel: View {
    @Environment(AppState.self) private var appState

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            PipelineStepBar()
            Divider()
            ActionBar()
            Divider()
            LogView()
        }
    }
}

// MARK: - Step bar

struct PipelineStepBar: View {
    @Environment(AppState.self) private var appState
    private let flow: [PipelineStep] = [.analyzing, .prompting, .generating, .reviewing, .complete]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(flow, id: \.self) { step in
                HStack(spacing: 4) {
                    Image(systemName: icon(for: step))
                        .foregroundStyle(color(for: step))
                    Text(step.rawValue)
                        .font(.caption)
                        .foregroundStyle(appState.currentStep == step ? .primary : .secondary)
                }
                .padding(.horizontal, 10).padding(.vertical, 8)

                if step != .complete {
                    Image(systemName: "chevron.right").font(.caption2).foregroundStyle(.tertiary)
                }
            }
        }
        .padding(.horizontal)
    }

    private func rank(_ s: PipelineStep) -> Int { flow.firstIndex(of: s) ?? -1 }
    private func icon(for step: PipelineStep) -> String {
        rank(appState.currentStep) > rank(step) ? "checkmark.circle.fill" : step.systemImage
    }
    private func color(for step: PipelineStep) -> Color {
        if appState.currentStep == step { return .blue }
        if rank(appState.currentStep) > rank(step) { return .green }
        return .gray
    }
}

// MARK: - Action bar

struct ActionBar: View {
    @Environment(AppState.self) private var appState

    private var canRun: Bool {
        !appState.isRunning && appState.moodboardPath != nil && !appState.products.isEmpty
    }

    var body: some View {
        HStack(spacing: 10) {
            StepButton(label: "Analyser",  icon: "photo.on.rectangle",  step: .analyzing)
            StepButton(label: "Prompt",    icon: "text.bubble",          step: .prompting)
            StepButton(label: "Générer",   icon: "wand.and.stars",       step: .generating)
            StepButton(label: "Revoir",    icon: "checkmark.seal",       step: .reviewing)

            Divider().frame(height: 24)

            Button {
                Task { await runFullPipeline() }
            } label: {
                Label(appState.isRunning ? "En cours..." : "Run complet", systemImage: "play.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(!canRun)

            if appState.isRunning { ProgressView().scaleEffect(0.7) }

            Spacer()

            Button {
                appState.clearLog()
                appState.currentStep = .idle
            } label: {
                Image(systemName: "trash")
            }
            .buttonStyle(.plain).foregroundStyle(.secondary)
            .help("Effacer le journal").disabled(appState.isRunning)
        }
        .padding(.horizontal).padding(.vertical, 10)
    }

    @MainActor
    private func runFullPipeline() async {
        let runner = PipelineRunner(pythonPath: appState.pythonPath, projectPath: appState.projectPath)
        appState.isRunning = true
        appState.clearLog()
        do {
            try await performAnalyze(runner, state: appState)
            try await performPrompt(runner, state: appState)
            try await performGenerate(runner, state: appState)
            try await performReview(runner, state: appState)
            appState.currentStep = .complete
        } catch {
            appState.appendLog("❌ \(error.localizedDescription)\n")
            appState.currentStep = .error
        }
        appState.isRunning = false
    }
}

// MARK: - Step button

struct StepButton: View {
    @Environment(AppState.self) private var appState
    let label: String
    let icon: String
    let step: PipelineStep

    var body: some View {
        Button {
            Task { await runStep() }
        } label: {
            Label(label, systemImage: icon)
        }
        .buttonStyle(.bordered)
        .disabled(appState.isRunning)
        .help("Lancer : \(label)")
    }

    @MainActor
    private func runStep() async {
        let runner = PipelineRunner(pythonPath: appState.pythonPath, projectPath: appState.projectPath)
        appState.isRunning = true
        appState.currentStep = step
        do {
            switch step {
            case .analyzing:  try await performAnalyze(runner, state: appState)
            case .prompting:  try await performPrompt(runner, state: appState)
            case .generating: try await performGenerate(runner, state: appState)
            case .reviewing:  try await performReview(runner, state: appState)
            default: break
            }
            appState.currentStep = .complete
        } catch {
            appState.appendLog("❌ \(error.localizedDescription)\n")
            appState.currentStep = .error
        }
        appState.isRunning = false
    }
}

// MARK: - Log view

struct LogView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                Text(appState.pipelineLog.isEmpty ? "En attente..." : appState.pipelineLog)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(appState.pipelineLog.isEmpty ? .tertiary : .primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(12)
                    .id("bottom")
            }
            .background(Color(NSColor.textBackgroundColor))
            .onChange(of: appState.pipelineLog) {
                withAnimation { proxy.scrollTo("bottom", anchor: .bottom) }
            }
        }
    }
}

// MARK: - Pipeline execution (shared helpers)

@MainActor
func performAnalyze(_ runner: PipelineRunner, state: AppState) async throws {
    guard let moodboard = state.moodboardPath else { throw PipelineError.noMoodboard }
    state.currentStep = .analyzing
    state.appendLog("▶ Analyse du moodboard...\n")
    let base       = URL(fileURLWithPath: state.projectPath)
    let outputPath = base.appendingPathComponent("data/prompts/analysis.json")
    let cmd = runner.buildAnalyzeCommand(moodboardPath: moodboard, outputPath: outputPath)
    let out = try await runner.run(command: cmd) { line in state.appendLog(line) }
    if let data = out.data(using: .utf8),
       let analysis = try? JSONDecoder().decode(StyleAnalysis.self, from: data) {
        state.styleAnalysis = analysis
    }
    state.appendLog("✓ Analyse terminée\n")
}

@MainActor
func performPrompt(_ runner: PipelineRunner, state: AppState) async throws {
    state.currentStep = .prompting
    state.appendLog("▶ Génération du prompt...\n")
    let base         = URL(fileURLWithPath: state.projectPath)
    let analysisPath = base.appendingPathComponent("data/prompts/analysis.json")
    let outputPath   = base.appendingPathComponent("data/prompts/master_prompt.json")
    try await runner.run(command: runner.buildPromptCommand(analysisPath: analysisPath, outputPath: outputPath)) { line in
        state.appendLog(line)
    }
    state.appendLog("✓ Prompt généré\n")
}

@MainActor
func performGenerate(_ runner: PipelineRunner, state: AppState) async throws {
    guard !state.products.isEmpty else { throw PipelineError.noProducts }
    state.currentStep = .generating
    state.appendLog("▶ Génération des images (\(state.products.count) produit(s))...\n")
    let base       = URL(fileURLWithPath: state.projectPath)
    let promptPath = base.appendingPathComponent("data/prompts/master_prompt.json")
    try await runner.run(command: runner.buildGenerateCommand(promptPath: promptPath, products: state.products, outputDir: state.outputPath)) { line in
        state.appendLog(line)
    }
    reloadGeneratedImages(state: state)
    state.appendLog("✓ Images générées : \(state.generatedImages.count)\n")
}

@MainActor
func performReview(_ runner: PipelineRunner, state: AppState) async throws {
    state.currentStep = .reviewing
    state.appendLog("▶ Revue qualité...\n")
    let base         = URL(fileURLWithPath: state.projectPath)
    let analysisPath = base.appendingPathComponent("data/prompts/analysis.json")
    let reportPath   = base.appendingPathComponent("data/prompts/review_report.json")
    try await runner.run(command: runner.buildReviewCommand(imagesDir: state.outputPath, analysisPath: analysisPath, outputPath: reportPath)) { line in
        state.appendLog(line)
    }
    state.appendLog("✓ Revue terminée\n")
}

func reloadGeneratedImages(state: AppState) {
    let exts   = Set(["png", "jpg", "jpeg"])
    let images = (try? FileManager.default.contentsOfDirectory(at: state.outputPath, includingPropertiesForKeys: nil))?
        .filter { exts.contains($0.pathExtension.lowercased()) }
        .compactMap { GeneratedImage.from(url: $0) }
        .sorted { $0.filename < $1.filename }
        ?? []
    state.generatedImages = images
}
