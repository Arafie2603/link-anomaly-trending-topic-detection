def extract_keywords(topics_dict):
    """
    Extract all unique keywords from topics dictionary.
    
    Parameters:
    topics_dict (dict): Dictionary of topics where each value is a list of (word, weight) tuples
    
    Returns:
    set: Set of unique keywords
    """
    keywords = set()
    for topic_words in topics_dict.values():
        keywords.update(word for word, _ in topic_words)
    return keywords

def calculate_topic_similarity(gt_topic, pred_topic, threshold=0.3):
    """
    Calculate similarity between two topics based on common keywords.
    
    Parameters:
    gt_topic (list): List of (word, weight) tuples for ground truth topic
    pred_topic (list): List of (word, weight) tuples for predicted topic
    threshold (float): Minimum similarity threshold to consider topics as matching
    
    Returns:
    float: Similarity score
    """
    gt_words = set(word for word, _ in gt_topic)
    pred_words = set(word for word, _ in pred_topic)
    
    common_words = gt_words.intersection(pred_words)
    
    if not gt_words or not pred_words:
        return 0.0
        
    similarity = len(common_words) / max(len(gt_words), len(pred_words))
    return similarity if similarity >= threshold else 0.0

def find_matching_topics(ground_truth, predictions, threshold=0.3):
    """
    Find matching topics between ground truth and predictions.
    
    Parameters:
    ground_truth (dict): Ground truth topics dictionary
    predictions (dict): Predicted topics dictionary
    threshold (float): Minimum similarity threshold
    
    Returns:
    set: Set of matched topic pairs (gt_topic_num, pred_topic_num)
    """
    matches = set()
    
    for gt_topic_num, gt_topic in ground_truth.items():
        for pred_topic_num, pred_topic in predictions.items():
            similarity = calculate_topic_similarity(gt_topic, pred_topic, threshold)
            if similarity > threshold:
                matches.add((gt_topic_num, pred_topic_num))
                
    return matches

def evaluate_topics(ground_truth, predictions, threshold=0.3):
    """
    Calculate Topic Recall (TR), Keyword Precision (KP), and Keyword Recall (KR).
    
    Parameters:
    ground_truth (dict): Ground truth topics dictionary
    predictions (dict): Predicted topics dictionary
    threshold (float): Minimum similarity threshold for topic matching
    
    Returns:
    dict: Dictionary containing TR, KP, and KR scores
    """
    # Extract all keywords
    gt_keywords = extract_keywords(ground_truth)
    pred_keywords = extract_keywords(predictions)
    
    # Find matching topics
    matching_topics = find_matching_topics(ground_truth, predictions, threshold)
    
    # Calculate Topic Recall (TR)
    tr = len(matching_topics) / len(ground_truth)
    
    # Calculate keyword intersection
    common_keywords = gt_keywords.intersection(pred_keywords)
    
    # Calculate Keyword Precision (KP) and Keyword Recall (KR)
    kp = len(common_keywords) / len(pred_keywords) if pred_keywords else 0
    kr = len(common_keywords) / len(gt_keywords) if gt_keywords else 0
    
    return {
        'Topic_Recall': tr,
        'Keyword_Precision': kp,
        'Keyword_Recall': kr
    }

# Example usage with your data
def main():
    # Ground truth topics
    ground_truth = {
        'Topik 1': [
            ('debat', 0.0068), ('pilkada', 0.0044), ('jateng', 0.0025),
            ('calon', 0.0011), ('petugas', 0.0011), ('cerita', 0.0011), ('bupati', 0.0011)
        ],
        'Topik 2': [
            ('pilkada', 0.0073), ('jakarta', 0.0047), ('kamil', 0.0027),
            ('ridwan', 0.0027), ('survei', 0.0027), ('persen', 0.0027),
            ('dki', 0.0012), ('pdip', 0.0012)
        ],
        'Topik 3': [
            ('pilkada', 0.0149), ('debat', 0.0118), ('digelar', 0.0030),
            ('perdana', 0.0030), ('kota', 0.0008), ('sumut', 0.0008),
            ('november', 0.0008), ('jelang', 0.0008), ('bekasi', 0.0008)
        ],
        'Topik 4': [
            ('pilkada', 0.0098), ('kota', 0.0063), ('debat', 0.0016),
            ('atasi', 0.0016), ('paslon', 0.0016), ('bandung', 0.0016),
            ('siapkan', 0.0016)
        ],
        'Topik 5': [
            ('pilkada', 0.0129), ('debat', 0.0024), ('solo', 0.0024),
            ('bawaslu', 0.0011), ('netralitas', 0.0011), ('wilayah', 0.0011)
        ]
    }

    # Model predictions
    predictions = {
        'Topik 1': [
            ('pilkada', 0.0072), ('debat', 0.0024), ('luthfi', 0.0012),
            ('dukung', 0.0010), ('calon', 0.0009), ('yasin', 0.0008),
            ('gus', 0.0007), ('gubernur', 0.0007), ('jateng', 0.0003),
            ('wakil', 0.0002)
        ],
        'Topik 2': [
            ('pilkada', 0.0085), ('politik', 0.0004), ('partai', 0.0004),
            ('pemilu', 0.0003), ('pilpres', 0.0002)
        ],
        'Topik 3': [
            ('pilkada', 0.0088), ('pilih', 0.0003), ('serentak', 0.0003),
            ('kota', 0.0003), ('kabupaten', 0.0003)
        ],
        'Topik 4': [
            ('pilkada', 0.0058), ('jakarta', 0.0013), ('calon', 0.0004),
            ('menang', 0.0003), ('pilih', 0.0002), ('bupati', 0.0002)
        ],
        'Topik 5': [
            ('pilkada', 0.0020), ('jokowi', 0.0007), ('anis', 0.0002)
        ]
    }

    # Calculate evaluation metrics
    results = evaluate_topics(ground_truth, predictions, threshold=0.3)
    
    # Print results
    print("\nEvaluation Results:")
    print(f"Topic Recall (TR): {results['Topic_Recall']:.4f}")
    print(f"Keyword Precision (KP): {results['Keyword_Precision']:.4f}")
    print(f"Keyword Recall (KR): {results['Keyword_Recall']:.4f}")

    # Print matching topics for analysis
    print("\nMatching Topics (similarity > 0.3):")
    matches = find_matching_topics(ground_truth, predictions, threshold=0.3)
    for gt_topic, pred_topic in matches:
        print(f"Ground Truth {gt_topic} matches with Predicted {pred_topic}")

if __name__ == "__main__":
    main()