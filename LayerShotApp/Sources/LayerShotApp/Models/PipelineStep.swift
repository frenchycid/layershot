import Foundation

public enum PipelineStep: String, CaseIterable, Equatable {
    case idle       = "Prêt"
    case analyzing  = "Analyse..."
    case prompting  = "Prompt..."
    case generating = "Génération..."
    case reviewing  = "Revue..."
    case complete   = "Terminé"
    case error      = "Erreur"

    var systemImage: String {
        switch self {
        case .idle:       return "circle"
        case .analyzing:  return "photo.on.rectangle"
        case .prompting:  return "text.bubble"
        case .generating: return "wand.and.stars"
        case .reviewing:  return "checkmark.seal"
        case .complete:   return "checkmark.circle.fill"
        case .error:      return "xmark.circle.fill"
        }
    }
}
