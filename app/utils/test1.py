# def initialize_bins(scores, NH):
#     a = np.mean(scores) + 2 * np.std(scores)  
#     b = np.min(scores)  
#     bin_edges = [-np.inf] + [b + (a - b) / (NH - 2) * i for i in range(NH - 2)] + [np.inf]
#     print(bin_edges)
#     return bin_edges, a, b

# def initialize_histogram(NH):
#     return np.ones(NH) / NH

# def update_histogram(histogram, bins, score, r_H, lambda_H):
#     bin_index = np.digitize(score, bins) - 1
#     updated_histogram = np.zeros_like(histogram)

#     for h in range(len(histogram)):
#         if h == bin_index:
#             updated_histogram[h] = (1 - r_H) * histogram[h] + r_H
#         else:
#             updated_histogram[h] = (1 - r_H) * histogram[h]
#     updated_histogram = (updated_histogram + lambda_H) / (np.sum(updated_histogram) + len(histogram) * lambda_H)
    
#     return updated_histogram

# def optimize_threshold(histogram, bins, rho):
#     cumulative_distribution = np.cumsum(histogram)
#     threshold_index = np.argmax(cumulative_distribution >= (1 - rho))
#     return bins[threshold_index]

# def process_session(scores, NH=20, rho=0.05, r_H=0.001, lambda_H=0.5):
#     bins, a, b = initialize_bins(scores, NH)
#     histogram = initialize_histogram(NH)
#     results = []
#     M = len(scores) - 1

#     for i in range(M):
#         histogram = update_histogram(histogram, bins, score, r_H, lambda_H)
#         threshold = optimize_threshold(histogram, bins, rho)
#         alarm = scores[i] >= threshold
#         print(f"{scores[i]} >= {threshold} = {alarm}")
#         results.append({"Session": i + 1, "Score": scores, "Threshold": threshold, "Alarm": alarm})
    
#     return results
# results = process_session(second_scores)